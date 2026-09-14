from __future__ import annotations

import os
from pathlib import Path

import numpy as np


def default_data_root() -> Path:
    env = os.getenv("ANOMALYMATRIX_DATA_ROOT", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "data"


def active_memory_bank_path(data_root: Path | None = None) -> Path:
    root = Path(data_root) if data_root is not None else default_data_root()
    return root / "training-artifacts" / "active_memory_bank.npz"


def iter_memory_bank_candidates(data_root: Path | None = None) -> list[Path]:
    """Search order for the active PatchCore memory bank."""
    custom = os.getenv("PATCHCORE_MEMORY_BANK", "").strip()
    paths: list[Path] = []
    if custom:
        paths.append(Path(custom))
    if data_root is not None:
        paths.append(active_memory_bank_path(data_root))
    default_path = active_memory_bank_path(default_data_root())
    if default_path not in paths:
        paths.append(default_path)
    # unique while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def frame_to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.uint8)
    if image.shape[2] == 4:
        image = image[:, :, :3]
    import cv2

    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def extract_embedding(gray: np.ndarray, *, size: int = 32) -> np.ndarray:
    import cv2

    resized = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    vec = resized.astype(np.float32).flatten() / 255.0
    norm = float(np.linalg.norm(vec)) or 1.0
    return vec / norm


def build_memory_bank(images: list[np.ndarray]) -> np.ndarray:
    if not images:
        raise ValueError("At least one training image required")
    rows = [extract_embedding(frame_to_grayscale(img)) for img in images]
    return np.stack(rows, axis=0)


def min_distance_score(features: np.ndarray, bank: np.ndarray) -> float:
    if bank.size == 0:
        return 0.0
    dists = np.linalg.norm(bank - features, axis=1)
    return float(np.min(dists))


def distance_to_anomaly_score(distance: float) -> float:
    return round(min(1.0, distance / 1.25), 4)


def save_memory_bank(path: Path, *, bank: np.ndarray, model_version: str, recipe_id: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, embeddings=bank, model_version=model_version, recipe_id=recipe_id)
    return str(path)


def load_memory_bank(path: str | Path) -> tuple[np.ndarray, dict]:
    data = np.load(path, allow_pickle=False)
    meta = {
        "model_version": str(data.get("model_version", "patchcore-trained")),
        "recipe_id": str(data.get("recipe_id", "recipe-default")),
    }
    return data["embeddings"], meta


def inspect_memory_bank(data_root: Path | None = None) -> dict:
    for path in iter_memory_bank_candidates(data_root):
        if not path.exists():
            continue
        try:
            bank, meta = load_memory_bank(path)
            return {
                "loaded": True,
                "path": str(path),
                "model_version": meta.get("model_version"),
                "recipe_id": meta.get("recipe_id"),
                "embedding_count": int(bank.shape[0]),
            }
        except Exception:
            continue
    return {
        "loaded": False,
        "path": None,
        "model_version": None,
        "recipe_id": None,
        "embedding_count": 0,
    }
