from __future__ import annotations

import os
from pathlib import Path

import numpy as np

LAYOUT_IMAGE = "image"
LAYOUT_PATCH_GRID = "patch_grid"
PATCH_GRID = 16
PATCH_EMBED_SIZE = 16


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
    """Legacy whole-image embedding (flattened, L2-normalized)."""
    import cv2

    resized = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    vec = resized.astype(np.float32).flatten() / 255.0
    norm = float(np.linalg.norm(vec)) or 1.0
    return vec / norm


def extract_patch_grid(
    gray: np.ndarray,
    *,
    grid: int = PATCH_GRID,
    embed_size: int = PATCH_EMBED_SIZE,
) -> np.ndarray:
    """Return (grid, grid, embed_size**2) local patch vectors in [0, 1] (brightness preserved)."""
    import cv2

    if gray.ndim != 2:
        gray = frame_to_grayscale(gray)
    canvas_side = int(grid) * int(embed_size)
    canvas = cv2.resize(gray, (canvas_side, canvas_side), interpolation=cv2.INTER_AREA)
    canvas = canvas.astype(np.float32) / 255.0
    tiled = canvas.reshape(grid, embed_size, grid, embed_size).transpose(0, 2, 1, 3)
    # Keep brightness: L2-normalizing constant patches would make a dark stain
    # indistinguishable from a uniform good-part body.
    return tiled.reshape(grid, grid, embed_size * embed_size).astype(np.float32)


def patch_min_distances(query_patches: np.ndarray, bank: np.ndarray) -> np.ndarray:
    """Min L2 to the memory bank per query patch. query: (..., D), bank: (M, D)."""
    spatial_shape = query_patches.shape[:-1]
    flat = np.ascontiguousarray(query_patches.reshape(-1, query_patches.shape[-1]), dtype=np.float32)
    bank_f = np.ascontiguousarray(bank, dtype=np.float32)
    # ||a-b||^2 = ||a||^2 + ||b||^2 - 2 a·b
    a2 = np.einsum("ij,ij->i", flat, flat)[:, None]
    b2 = np.einsum("ij,ij->i", bank_f, bank_f)[None, :]
    dots = flat @ bank_f.T
    dists = np.sqrt(np.maximum(0.0, a2 + b2 - 2.0 * dots))
    return dists.min(axis=1).reshape(spatial_shape)


def upsample_anomaly_map(small: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    import cv2

    height, width = int(hw[0]), int(hw[1])
    up = cv2.resize(small.astype(np.float32), (width, height), interpolation=cv2.INTER_CUBIC)
    sigma = max(1.0, min(height, width) / 64.0)
    return cv2.GaussianBlur(up, (0, 0), sigma)


def build_memory_bank(
    images: list[np.ndarray],
    *,
    grid: int = PATCH_GRID,
    embed_size: int = PATCH_EMBED_SIZE,
) -> np.ndarray:
    if not images:
        raise ValueError("At least one training image required")
    rows = [
        extract_patch_grid(frame_to_grayscale(img), grid=grid, embed_size=embed_size).reshape(-1, embed_size * embed_size)
        for img in images
    ]
    return np.concatenate(rows, axis=0)


def min_distance_score(features: np.ndarray, bank: np.ndarray) -> float:
    if bank.size == 0:
        return 0.0
    dists = np.linalg.norm(bank - features, axis=1)
    return float(np.min(dists))


def distance_to_anomaly_score(distance: float) -> float:
    return round(min(1.0, distance / 1.25), 4)


def default_patch_bank_meta() -> dict:
    return {
        "layout": LAYOUT_PATCH_GRID,
        "grid": PATCH_GRID,
        "patch_embed_size": PATCH_EMBED_SIZE,
    }


def infer_spatial(
    gray: np.ndarray,
    bank: np.ndarray,
    meta: dict | None = None,
) -> tuple[float, np.ndarray | None, str]:
    """Score plus spatial anomaly map aligned to ``gray``.

    Returns (anomaly_score, map_or_none, heatmap_kind) where kind is
    ``patchcore``, ``legacy_spatial``, or ``residual``.
    """
    meta = meta or {}
    layout = str(meta.get("layout") or LAYOUT_IMAGE)
    if gray.ndim != 2:
        gray = frame_to_grayscale(gray)
    if bank is None or getattr(bank, "size", 0) == 0:
        return 0.0, None, "residual"

    if layout == LAYOUT_PATCH_GRID and bank.ndim == 2:
        grid = int(meta.get("grid") or PATCH_GRID)
        embed_size = int(meta.get("patch_embed_size") or PATCH_EMBED_SIZE)
        expected_dim = embed_size * embed_size
        if bank.shape[1] == expected_dim:
            query = extract_patch_grid(gray, grid=grid, embed_size=embed_size)
            dist_grid = patch_min_distances(query, bank)
            score = distance_to_anomaly_score(float(np.max(dist_grid)))
            return score, upsample_anomaly_map(dist_grid, gray.shape[:2]), "patchcore"

    features = extract_embedding(gray)
    if bank.ndim == 2 and bank.shape[1] == features.shape[0]:
        distance = min_distance_score(features, bank)
        score = distance_to_anomaly_score(distance)
        spatial = _legacy_nn_residual_map(gray, features, bank)
        return score, spatial, "legacy_spatial" if spatial is not None else "residual"

    return 0.0, None, "residual"


def _legacy_nn_residual_map(gray: np.ndarray, features: np.ndarray, bank: np.ndarray) -> np.ndarray | None:
    """Pixel residual vs nearest whole-image embedding (legacy banks)."""
    if bank.size == 0:
        return None
    dists = np.linalg.norm(bank.astype(np.float32) - features.astype(np.float32), axis=1)
    nearest = bank[int(np.argmin(dists))].astype(np.float32)
    dim = int(features.size)
    side = int(np.sqrt(dim))
    if side * side != dim:
        return None
    residual = np.abs(features.reshape(side, side) - nearest.reshape(side, side))
    return upsample_anomaly_map(residual, gray.shape[:2])


def save_memory_bank(
    path: Path,
    *,
    bank: np.ndarray,
    model_version: str,
    recipe_id: str,
    layout: str = LAYOUT_PATCH_GRID,
    grid: int = PATCH_GRID,
    patch_embed_size: int = PATCH_EMBED_SIZE,
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        embeddings=bank,
        model_version=np.asarray(model_version),
        recipe_id=np.asarray(recipe_id),
        layout=np.asarray(layout),
        grid=np.int32(grid),
        patch_embed_size=np.int32(patch_embed_size),
    )
    return str(path)


def _npz_scalar(data, key: str, default):
    files = getattr(data, "files", None)
    if files is not None and key not in files:
        return default
    try:
        value = data[key]
    except (KeyError, ValueError):
        return default
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return value.item()
        if value.size == 1:
            return value.reshape(()).item()
    return value


def load_memory_bank(path: str | Path) -> tuple[np.ndarray, dict]:
    data = np.load(path, allow_pickle=False)
    files = set(getattr(data, "files", []))
    # Banks without a layout key are the pre-patch format (one 32×32 image vector).
    if "layout" in files:
        layout = str(_npz_scalar(data, "layout", LAYOUT_IMAGE) or LAYOUT_IMAGE)
    else:
        layout = LAYOUT_IMAGE
    if layout not in {LAYOUT_IMAGE, LAYOUT_PATCH_GRID}:
        layout = LAYOUT_IMAGE
    grid = int(_npz_scalar(data, "grid", PATCH_GRID) or PATCH_GRID)
    patch_embed_size = int(_npz_scalar(data, "patch_embed_size", PATCH_EMBED_SIZE) or PATCH_EMBED_SIZE)
    embeddings = data["embeddings"]
    meta = {
        "model_version": str(_npz_scalar(data, "model_version", "patchcore-trained")),
        "recipe_id": str(_npz_scalar(data, "recipe_id", "recipe-default")),
        "layout": layout,
        "grid": grid,
        "patch_embed_size": patch_embed_size,
    }
    return embeddings, meta


def inspect_memory_bank(data_root: Path | None = None) -> dict:
    for path in iter_memory_bank_candidates(data_root):
        if not path.exists():
            continue
        try:
            bank, meta = load_memory_bank(path)
            layout = str(meta.get("layout") or LAYOUT_IMAGE)
            return {
                "loaded": True,
                "path": str(path),
                "model_version": meta.get("model_version"),
                "recipe_id": meta.get("recipe_id"),
                "embedding_count": int(bank.shape[0]),
                "embedding_dim": int(bank.shape[1]) if bank.ndim == 2 else 0,
                "layout": layout,
                "grid": meta.get("grid"),
                "patch_embed_size": meta.get("patch_embed_size"),
                "localization_ready": layout == LAYOUT_PATCH_GRID,
            }
        except Exception:
            continue
    return {
        "loaded": False,
        "path": None,
        "model_version": None,
        "recipe_id": None,
        "embedding_count": 0,
        "embedding_dim": 0,
        "layout": None,
        "grid": None,
        "patch_embed_size": None,
        "localization_ready": False,
    }
