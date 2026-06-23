from __future__ import annotations

from pathlib import Path

import numpy as np


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
