from __future__ import annotations

from pathlib import Path

import numpy as np

from .nio_store import safe_id


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


def generate_heatmap_png(gray: np.ndarray, anomaly_score: float) -> bytes:
    """Production heatmap overlay (OpenCV jet on high-frequency residual)."""
    try:
        import cv2
    except ImportError:
        return _fallback_png(gray)

    if gray.ndim != 2:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0, 0), 2.0)
    residual = cv2.absdiff(gray, blur)
    residual = cv2.normalize(residual, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(residual, cv2.COLORMAP_JET)
    alpha = min(0.85, max(0.25, float(anomaly_score)))
    overlay = cv2.addWeighted(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), 1.0 - alpha, heat, alpha, 0)
    ok, buf = cv2.imencode(".png", overlay)
    if not ok:
        return _fallback_png(gray)
    return buf.tobytes()


def _fallback_png(gray: np.ndarray) -> bytes:
    try:
        import cv2
    except ImportError:
        return b""
    ok, buf = cv2.imencode(".png", gray)
    return buf.tobytes() if ok else b""
