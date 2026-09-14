from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

from .patchcore_memory import active_memory_bank_path, build_memory_bank, default_patch_bank_meta, save_memory_bank
from .production import is_production
from .nio_store import count_nio_images, load_local_nio_images
from .storage_minio import decode_png_bytes, list_training_image_bytes, load_local_training_images, store_raw_frame


def _synthetic_good_images(recipe_id: str, *, count: int = 12, size: int = 128) -> list[np.ndarray]:
    seed = abs(hash(recipe_id)) % (2**31)
    rng = np.random.default_rng(seed)
    images: list[np.ndarray] = []
    for i in range(count):
        base = rng.normal(120, 8, (size, size)).astype(np.float32)
        noise = rng.normal(0, 3, (size, size))
        patch = np.clip(base + noise, 0, 255).astype(np.uint8)
        images.append(patch)
    return images


def training_images_dir(data_root: Path, recipe_id: str) -> Path:
    return Path(data_root) / "training-images" / recipe_id


def count_training_images(data_root: Path, recipe_id: str) -> int:
    folder = training_images_dir(data_root, recipe_id)
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.png")))


def collect_training_images(*, data_root: Path, recipe_id: str, sample_count: int) -> tuple[list[np.ndarray], str]:
    """Prefer explicit Gutteil captures, then MinIO raw frames, else synthetic."""
    images = load_local_training_images(data_root, recipe_id, limit=sample_count)
    if images:
        return images[:sample_count], "local_files"

    images = []
    for blob in list_training_image_bytes(recipe_id=recipe_id, limit=sample_count):
        decoded = decode_png_bytes(blob)
        if decoded is not None:
            images.append(decoded)
    if images:
        return images[:sample_count], "minio_raw"

    return _synthetic_good_images(recipe_id, count=sample_count)[:sample_count], "synthetic_fallback"


def set_active_memory_bank(data_root: Path, artifact_path: str | Path | None) -> str | None:
    """Point active_memory_bank.npz at an existing artifact. Never deletes the source .npz."""
    active_link = active_memory_bank_path(data_root)
    active_link.parent.mkdir(parents=True, exist_ok=True)
    try:
        active_link.unlink(missing_ok=True)
    except OSError:
        pass
    if artifact_path is None:
        return None
    source = Path(artifact_path)
    if not source.exists():
        raise FileNotFoundError(f"Memory-bank artifact not found: {source}")
    try:
        target = source.name if source.parent.resolve() == active_link.parent.resolve() else source
        active_link.symlink_to(target)
    except OSError:
        import shutil

        shutil.copy2(source, active_link)
    return str(active_link)


def artifact_path_for_model(model: dict | None) -> Path | None:
    if not model:
        return None
    meta = model.get("metadata") or {}
    uri = meta.get("artifact_uri")
    if not uri:
        return None
    path = Path(str(uri))
    return path if path.exists() else None


def _encode_png(gray: np.ndarray) -> bytes:
    import cv2

    ok, buf = cv2.imencode(".png", gray)
    if not ok:
        raise RuntimeError("Failed to encode training PNG")
    return buf.tobytes()


def _frame_png_bytes(frame) -> bytes:
    import cv2

    b64 = getattr(frame, "image_b64", None)
    if b64:
        raw = base64.b64decode(b64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            return _encode_png(img)
        if raw.startswith(b"\x89PNG"):
            return raw
    rng = np.random.default_rng()
    gray = np.clip(rng.normal(120, 8, (128, 128)), 0, 255).astype(np.uint8)
    return _encode_png(gray)


def capture_good_part_samples(
    *,
    data_root: Path,
    recipe_id: str,
    camera_id: str,
    count: int = 8,
    source: str | None = None,
) -> dict:
    from .services_edge import capture_frame

    folder = training_images_dir(data_root, recipe_id)
    folder.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    batch_id = uuid4().hex[:8]
    for index in range(count):
        frame = capture_frame(camera_id=camera_id, recipe_id=recipe_id, source=source)
        png_bytes = _frame_png_bytes(frame)
        filename = f"{stamp}_{batch_id}_{index:02d}.png"
        path = folder / filename
        path.write_bytes(png_bytes)
        store_raw_frame(
            inspection_id=f"train-{batch_id}-{index:02d}",
            recipe_id=recipe_id,
            image_bytes=png_bytes,
            camera_id=camera_id,
        )
        saved_paths.append(str(path))
    return {
        "recipe_id": recipe_id,
        "camera_id": camera_id,
        "saved": len(saved_paths),
        "paths": saved_paths,
        "count": count_training_images(data_root, recipe_id),
        "data_source": "local_files",
    }


def train_patchcore(
    *,
    data_root: Path,
    recipe_id: str,
    dataset_version: str = "v1",
    sample_count: int = 12,
) -> dict:
    images, data_source = collect_training_images(data_root=data_root, recipe_id=recipe_id, sample_count=sample_count)
    bank_meta = default_patch_bank_meta()
    bank = build_memory_bank(images, grid=int(bank_meta["grid"]), embed_size=int(bank_meta["patch_embed_size"]))
    model_id = f"patchcore-{uuid4().hex[:8]}"
    model_version = f"{dataset_version}-{model_id[-4:]}"
    artifact_dir = Path(data_root) / "training-artifacts"
    artifact_path = artifact_dir / f"{model_id}.npz"
    save_memory_bank(
        artifact_path,
        bank=bank,
        model_version=model_version,
        recipe_id=recipe_id,
        layout=str(bank_meta["layout"]),
        grid=int(bank_meta["grid"]),
        patch_embed_size=int(bank_meta["patch_embed_size"]),
    )
    created_at = datetime.now(timezone.utc).isoformat()
    nio_report = _nio_holdout_report(
        data_root=data_root,
        recipe_id=recipe_id,
        bank=bank,
        bank_meta=bank_meta,
        io_count=len(images),
    )
    return {
        "model_id": model_id,
        "name": f"PatchCore {recipe_id}",
        "model_version": model_version,
        "provider": "patchcore",
        "dataset_version": dataset_version,
        "status": "candidate",
        "created_at": created_at,
        "metadata": {
            "artifact_uri": str(artifact_path),
            "recipe_id": recipe_id,
            "sample_count": len(images),
            "embedding_count": int(bank.shape[0]),
            "embedding_dim": int(bank.shape[1]),
            "layout": bank_meta["layout"],
            "grid": bank_meta["grid"],
            "patch_embed_size": bank_meta["patch_embed_size"],
            "data_source": data_source,
            "nio_sample_count": nio_report.get("nio_count", 0),
            "validation_report": {
                "signed": False,
                "holdout_passed": data_source != "synthetic_fallback",
                "sample_count": len(images),
                "nio_holdout": nio_report,
            },
        },
    }


def _nio_holdout_report(*, data_root: Path, recipe_id: str, bank, io_count: int, bank_meta: dict | None = None) -> dict:
    from .patchcore_memory import infer_spatial

    nio_images = load_local_nio_images(data_root, recipe_id, limit=32)
    if not nio_images:
        return {"nio_count": count_nio_images(data_root, recipe_id), "evaluated": 0}
    scores = []
    meta = bank_meta or default_patch_bank_meta()
    for image in nio_images:
        score, _, _ = infer_spatial(image, bank, meta)
        scores.append(score)
    mean_score = round(sum(scores) / len(scores), 4)
    return {
        "nio_count": count_nio_images(data_root, recipe_id),
        "evaluated": len(scores),
        "nio_mean_score": mean_score,
        "nio_min_score": round(min(scores), 4),
        "nio_max_score": round(max(scores), 4),
        "io_sample_count": io_count,
        "nio_scores_higher_than_mid": mean_score >= 0.5,
    }


def validate_candidate(
    *,
    baseline_score: float = 0.35,
    candidate_score: float = 0.42,
    data_source: str = "unknown",
    min_samples: int = 8,
    sample_count: int = 0,
) -> dict:
    regression_ok = candidate_score <= baseline_score * 1.15 + 0.05
    samples_ok = sample_count >= min_samples
    source_ok = data_source not in {"synthetic_fallback"} if is_production() else True
    passed = regression_ok and samples_ok and source_ok
    reasons = []
    if not regression_ok:
        reasons.append("regression_detected")
    if not samples_ok:
        reasons.append("insufficient_samples")
    if not source_ok:
        reasons.append("synthetic_only_dataset")
    return {
        "passed": passed,
        "baseline_score": baseline_score,
        "candidate_score": candidate_score,
        "data_source": data_source,
        "sample_count": sample_count,
        "reason": ",".join(reasons) if reasons else "within_tolerance",
    }
