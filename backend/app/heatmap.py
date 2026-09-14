from __future__ import annotations

from pathlib import Path

import numpy as np

from .decision import DEFAULT_THRESHOLDS, normalize_thresholds
from .nio_store import safe_id

HEATMAP_KIND_PATCHCORE = "patchcore"
HEATMAP_KIND_LEGACY = "legacy_spatial"
HEATMAP_KIND_RESIDUAL = "residual"

# Overlay opacity at the recipe amber / red scores (0 = raw image).
_ALPHA_AMBER = 0.45
_ALPHA_RED = 0.85
_COOL_FRACTION_OF_AMBER = 0.45
_NOISE_FLOOR_FRACTION_OF_AMBER = 0.15
# BGR amber (review) → hot red (NOK). Not OpenCV JET (relative 0–255 stretch).
_AMBER_BGR = (0.0, 191.0, 255.0)
_RED_BGR = (0.0, 16.0, 255.0)


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
    amber: float | None = None,
    red: float | None = None,
    thresholds: dict | None = None,
) -> bytes:
    """Threshold-calibrated overlay, not per-image min-max / JET stretch.

    Spatial maps (and residual fallback) are aligned so the peak matches the
    reported anomaly score, then colored against amber/red:
    well below amber is mostly the raw image; around amber is yellow/amber;
    at/above red is hot red.
    """
    try:
        import cv2
    except ImportError:
        return _fallback_png(gray)

    if gray.ndim != 2:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    amber_v, red_v = _resolve_thresholds(amber=amber, red=red, thresholds=thresholds)
    if anomaly_map is not None:
        overlay = _overlay_spatial_map(gray, anomaly_map, anomaly_score, amber_v, red_v)
    else:
        overlay = _residual_overlay(gray, anomaly_score, amber=amber_v, red=red_v)
    if overlay is None:
        return _fallback_png(gray)
    ok, buf = cv2.imencode(".png", overlay)
    if not ok:
        return _fallback_png(gray)
    return buf.tobytes()


def _resolve_thresholds(
    *,
    amber: float | None,
    red: float | None,
    thresholds: dict | None,
) -> tuple[float, float]:
    raw = dict(DEFAULT_THRESHOLDS)
    if isinstance(thresholds, dict):
        raw.update(thresholds)
    if amber is not None:
        raw["amber"] = amber
    if red is not None:
        raw["red"] = red
    norm = normalize_thresholds(raw)
    return float(norm["amber"]), float(norm["red"])


def _align_map_to_score(amap: np.ndarray, anomaly_score: float) -> np.ndarray:
    """Put a spatial map into the same units as the global anomaly score.

    Peak of the map equals the reported score so coloring tracks the
    inspection decision rather than the map's own dynamic range.
    """
    amap = np.asarray(amap, dtype=np.float32)
    finite = np.isfinite(amap)
    work = np.where(finite, np.maximum(amap, 0.0), 0.0).astype(np.float32)
    peak = float(np.max(work)) if work.size else 0.0
    score = max(0.0, float(anomaly_score))
    if peak > 1e-12:
        return (work * (score / peak)).astype(np.float32)
    return np.zeros_like(work, dtype=np.float32)


def _suppress_noise_floor(score_map: np.ndarray, amber: float) -> np.ndarray:
    """Subtract a light percentile floor without stretching to full range."""
    finite = np.isfinite(score_map)
    if not np.any(finite):
        return score_map
    p10 = float(np.percentile(score_map[finite], 10.0))
    floor = min(max(p10, 0.0), max(float(amber), 0.0) * _NOISE_FLOOR_FRACTION_OF_AMBER)
    if floor <= 0.0:
        return score_map
    return np.clip(score_map - floor, 0.0, None).astype(np.float32)


def _heat_from_scores(score_map: np.ndarray, amber: float, red: float) -> tuple[np.ndarray, np.ndarray]:
    """Map absolute scores to [0,1] heat (amber→red) and overlay alpha."""
    amber = max(float(amber), 1e-6)
    red = max(float(red), amber + 1e-6)
    cool = amber * _COOL_FRACTION_OF_AMBER
    scores = np.asarray(score_map, dtype=np.float32)

    t_cool = np.clip((scores - cool) / max(amber - cool, 1e-6), 0.0, 1.0)
    t_hot = np.clip((scores - amber) / max(red - amber, 1e-6), 0.0, 1.0)

    heat = np.zeros_like(scores, dtype=np.float32)
    alpha = np.zeros_like(scores, dtype=np.float32)

    visible = scores > cool
    below_amber = visible & (scores < amber)
    mid = (scores >= amber) & (scores < red)
    nio = scores >= red

    # 0 = amber/yellow, 1 = hot red. Below amber stays amber-colored; alpha carries strength.
    heat = np.where(mid, t_hot, heat)
    heat = np.where(nio, np.float32(1.0), heat)

    alpha = np.where(below_amber, np.float32(_ALPHA_AMBER) * t_cool, alpha)
    alpha = np.where(mid, np.float32(_ALPHA_AMBER + (_ALPHA_RED - _ALPHA_AMBER) * t_hot), alpha)
    alpha = np.where(nio, np.float32(_ALPHA_RED), alpha)
    return np.clip(heat, 0.0, 1.0), np.clip(alpha, 0.0, _ALPHA_RED)


def _amber_to_red_bgr(heat_01: np.ndarray) -> np.ndarray:
    """Absolute amber→red colors. Independent of per-image JET stretching."""
    t = np.clip(np.asarray(heat_01, dtype=np.float32), 0.0, 1.0)[..., None]
    amber = np.array(_AMBER_BGR, dtype=np.float32)
    red = np.array(_RED_BGR, dtype=np.float32)
    return np.clip(amber + (red - amber) * t, 0, 255).astype(np.uint8)


def _blend_heat(gray: np.ndarray, score_map: np.ndarray, amber: float, red: float) -> np.ndarray:
    import cv2

    heat_01, alpha = _heat_from_scores(score_map, amber, red)
    heat = _amber_to_red_bgr(heat_01)
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).astype(np.float32)
    alpha_f = alpha.astype(np.float32)[..., None]
    overlay = bgr * (1.0 - alpha_f) + heat.astype(np.float32) * alpha_f
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _overlay_spatial_map(
    gray: np.ndarray,
    anomaly_map: np.ndarray,
    anomaly_score: float,
    amber: float,
    red: float,
) -> np.ndarray | None:
    import cv2

    amap = np.asarray(anomaly_map, dtype=np.float32)
    if amap.ndim != 2:
        return None
    if amap.shape != gray.shape:
        amap = cv2.resize(amap, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_CUBIC)
    score_map = _align_map_to_score(amap, anomaly_score)
    score_map = _suppress_noise_floor(score_map, amber)
    return _blend_heat(gray, score_map, amber, red)


def _residual_overlay(gray: np.ndarray, anomaly_score: float, *, amber: float, red: float) -> np.ndarray | None:
    """Non-model fallback: high-frequency residual, score-gated to thresholds.

    Residual structure is used only for localization. Intensity follows the
    global score vs amber/red so an i.O. part is not min-maxed to full red.
    """
    import cv2

    blur = cv2.GaussianBlur(gray, (0, 0), 2.0)
    residual = cv2.absdiff(gray, blur).astype(np.float32)
    finite = np.isfinite(residual)
    if not np.any(finite):
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    p98 = float(np.percentile(residual[finite], 98.0))
    if p98 <= 1e-6:
        local = np.zeros_like(residual, dtype=np.float32)
    else:
        # Light percentile for structure only — do not force full colormap range.
        local = np.clip(residual / p98, 0.0, 1.0)
    score_map = _align_map_to_score(local, anomaly_score)
    score_map = _suppress_noise_floor(score_map, amber)
    return _blend_heat(gray, score_map, amber, red)


def _fallback_png(gray: np.ndarray) -> bytes:
    try:
        import cv2
    except ImportError:
        return b""
    ok, buf = cv2.imencode(".png", gray)
    return buf.tobytes() if ok else b""
