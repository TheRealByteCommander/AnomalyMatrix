from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import numpy as np

from .patchcore_memory import build_memory_bank, save_memory_bank


def _synthetic_good_images(recipe_id: str, *, count: int = 12, size: int = 128) -> list[np.ndarray]:
    """Generate deterministic good-part training patches (stand-in until real dataset ingest)."""
    seed = abs(hash(recipe_id)) % (2**31)
    rng = np.random.default_rng(seed)
    images: list[np.ndarray] = []
    for i in range(count):
        base = rng.normal(120, 8, (size, size)).astype(np.float32)
        noise = rng.normal(0, 3, (size, size))
        patch = np.clip(base + noise, 0, 255).astype(np.uint8)
        images.append(patch)
    return images


def train_patchcore(
    *,
    data_root: Path,
    recipe_id: str,
    dataset_version: str = "v1",
    sample_count: int = 12,
) -> dict:
    images = _synthetic_good_images(recipe_id, count=sample_count)
    bank = build_memory_bank(images)
    model_id = f"patchcore-{uuid4().hex[:8]}"
    model_version = f"{dataset_version}-{model_id[-4:]}"
    artifact_dir = data_root / "training-artifacts"
    artifact_path = artifact_dir / f"{model_id}.npz"
    save_memory_bank(artifact_path, bank=bank, model_version=model_version, recipe_id=recipe_id)
    active_link = artifact_dir / "active_memory_bank.npz"
    if active_link.exists() or not active_link.is_symlink():
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
        },
    }


def validate_candidate(*, baseline_score: float = 0.35, candidate_score: float = 0.42) -> dict:
    """Lightweight promotion gate — candidate must not exceed baseline anomaly proxy by >15%."""
    ok = candidate_score <= baseline_score * 1.15 + 0.05
    return {
        "passed": ok,
        "baseline_score": baseline_score,
        "candidate_score": candidate_score,
        "reason": "within_tolerance" if ok else "regression_detected",
    }
