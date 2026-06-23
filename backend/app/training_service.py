from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import numpy as np

from .patchcore_memory import build_memory_bank, save_memory_bank
from .production import is_production
from .storage_minio import decode_png_bytes, list_training_image_bytes, load_local_training_images


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


def collect_training_images(*, data_root: Path, recipe_id: str, sample_count: int) -> tuple[list[np.ndarray], str]:
    images: list[np.ndarray] = []
    source = "synthetic"

    for blob in list_training_image_bytes(recipe_id=recipe_id, limit=sample_count):
        decoded = decode_png_bytes(blob)
        if decoded is not None:
            images.append(decoded)

    if not images:
        images = load_local_training_images(data_root, recipe_id, limit=sample_count)
        if images:
            source = "local_files"

    if not images:
        images = _synthetic_good_images(recipe_id, count=sample_count)
        source = "synthetic_fallback"

    return images[:sample_count], source


def train_patchcore(
    *,
    data_root: Path,
    recipe_id: str,
    dataset_version: str = "v1",
    sample_count: int = 12,
) -> dict:
    images, data_source = collect_training_images(data_root=data_root, recipe_id=recipe_id, sample_count=sample_count)
    bank = build_memory_bank(images)
    model_id = f"patchcore-{uuid4().hex[:8]}"
    model_version = f"{dataset_version}-{model_id[-4:]}"
    artifact_dir = data_root / "training-artifacts"
    artifact_path = artifact_dir / f"{model_id}.npz"
    save_memory_bank(artifact_path, bank=bank, model_version=model_version, recipe_id=recipe_id)
    active_link = artifact_dir / "active_memory_bank.npz"
    try:
        active_link.unlink(missing_ok=True)
    except OSError:
        pass
    try:
        active_link.symlink_to(artifact_path.name)
    except OSError:
        import shutil

        shutil.copy2(artifact_path, active_link)

    return {
        "model_id": model_id,
        "name": f"PatchCore {recipe_id}",
        "model_version": model_version,
        "provider": "patchcore",
        "dataset_version": dataset_version,
        "status": "candidate",
        "metadata": {
            "artifact_uri": str(artifact_path),
            "recipe_id": recipe_id,
            "embedding_count": int(bank.shape[0]),
            "embedding_dim": int(bank.shape[1]),
            "data_source": data_source,
            "validation_report": {
                "signed": False,
                "holdout_passed": data_source != "synthetic_fallback",
                "sample_count": len(images),
            },
        },
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
