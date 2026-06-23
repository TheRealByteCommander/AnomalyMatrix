from __future__ import annotations

import io

import numpy as np


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
