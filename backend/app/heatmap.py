from __future__ import annotations

from pathlib import Path

import numpy as np

from .nio_store import safe_id

HEATMAP_KIND_PATCHCORE = "patchcore"
HEATMAP_KIND_LEGACY = "legacy_spatial"
HEATMAP_KIND_RESIDUAL = "residual"


def heatmap_dir(data_root: Path, inspection_id: str) -> Path:
    return Path(data_root) / "heatmaps" / safe_id(inspection_id)


def heatmap_api_uri(inspection_id: str, camera_id: str) -> str:
    return f"/api/v1/inspections/{inspection_id}/heatmap?camera_id={safe_id(camera_id, fallback='cam')}"


def save_local_heatmap(
    *,
    data_root: Path,
    inspection_id: str,
    camera_id: str,
    png_bytes: bytes,
) -> Path | None:
    if not png_bytes:
        return None
    folder = heatmap_dir(data_root, inspection_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_id(camera_id, fallback='cam')}.png"
    path.write_bytes(png_bytes)
    return path


def load_local_heatmap(data_root: Path, inspection_id: str, camera_id: str | None = None) -> Path | None:
    folder = heatmap_dir(data_root, inspection_id)
    if not folder.exists():
        return None
    if camera_id:
        path = folder / f"{safe_id(camera_id, fallback='cam')}.png"
        if path.exists():
            return path
    pngs = sorted(folder.glob("*.png"))
    return pngs[0] if pngs else None


def generate_heatmap_png(
    gray: np.ndarray,
    anomaly_score: float,
    *,
    anomaly_map: np.ndarray | None = None,
) -> bytes:
    """Jet overlay. Prefer a spatial model map; Gaussian residual is last resort."""
    try:
        import cv2
    except ImportError:
        return _fallback_png(gray)

    if gray.ndim != 2:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    if anomaly_map is not None:
        overlay = _overlay_spatial_map(gray, anomaly_map)
    else:
        overlay = _residual_overlay(gray, anomaly_score)
    if overlay is None:
        return _fallback_png(gray)
    ok, buf = cv2.imencode(".png", overlay)
    if not ok:
        return _fallback_png(gray)
    return buf.tobytes()


def _percentile_stretch(amap: np.ndarray) -> np.ndarray:
    amap = np.asarray(amap, dtype=np.float32)
    finite = np.isfinite(amap)
    if not np.any(finite):
        return np.zeros_like(amap, dtype=np.float32)
    lo, hi = np.percentile(amap[finite], [10.0, 98.0])
    if not np.isfinite(hi) or hi <= lo:
        hi = float(lo + 1e-6)
    stretched = np.clip((amap - lo) / (hi - lo), 0.0, 1.0)
    # Suppress floor; lift true hotspots so jet red/yellow is visible on dark defects.
    stretched = np.where(stretched < 0.28, stretched * 0.08, stretched)
    return np.clip(np.power(stretched, 0.65), 0.0, 1.0).astype(np.float32)


def _overlay_spatial_map(gray: np.ndarray, anomaly_map: np.ndarray) -> np.ndarray | None:
    import cv2

    amap = np.asarray(anomaly_map, dtype=np.float32)
    if amap.ndim != 2:
        return None
    if amap.shape != gray.shape:
        amap = cv2.resize(amap, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_CUBIC)
    stretched = _percentile_stretch(amap)
    heat_u8 = np.clip(stretched * 255.0, 0, 255).astype(np.uint8)
    heat = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).astype(np.float32)
    alpha = (stretched * 0.85).astype(np.float32)[..., None]
    overlay = bgr * (1.0 - alpha) + heat.astype(np.float32) * alpha
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _residual_overlay(gray: np.ndarray, anomaly_score: float) -> np.ndarray | None:
    """Non-model fallback: high-frequency residual, locally alpha-scaled."""
    import cv2

    blur = cv2.GaussianBlur(gray, (0, 0), 2.0)
    residual = cv2.absdiff(gray, blur)
    residual = cv2.normalize(residual, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(residual, cv2.COLORMAP_JET)
    local = residual.astype(np.float32) / 255.0
    gain = min(0.7, max(0.2, float(anomaly_score)))
    alpha = (local * gain).astype(np.float32)[..., None]
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).astype(np.float32)
    overlay = bgr * (1.0 - alpha) + heat.astype(np.float32) * alpha
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _fallback_png(gray: np.ndarray) -> bytes:
    try:
        import cv2
    except ImportError:
        return b""
    ok, buf = cv2.imencode(".png", gray)
    return buf.tobytes() if ok else b""
