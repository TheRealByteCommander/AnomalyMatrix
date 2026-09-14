from __future__ import annotations

DEFAULT_AMBER_THRESHOLD = 0.55
DEFAULT_RED_THRESHOLD = 0.85
DEFAULT_THRESHOLDS = {"amber": DEFAULT_AMBER_THRESHOLD, "red": DEFAULT_RED_THRESHOLD}


def normalize_thresholds(raw: dict | None) -> dict:
    payload = raw if isinstance(raw, dict) else {}
    try:
        amber = float(payload.get("amber", DEFAULT_AMBER_THRESHOLD))
    except (TypeError, ValueError):
        amber = DEFAULT_AMBER_THRESHOLD
    try:
        red = float(payload.get("red", DEFAULT_RED_THRESHOLD))
    except (TypeError, ValueError):
        red = DEFAULT_RED_THRESHOLD
    amber = min(max(amber, 0.0), 1.0)
    red = min(max(red, 0.0), 1.0)
    if red <= amber:
        red = min(1.0, amber + 0.01)
    return {"amber": round(amber, 4), "red": round(red, 4)}


def validate_thresholds(amber: float, red: float) -> dict:
    try:
        amber_f = float(amber)
        red_f = float(red)
    except (TypeError, ValueError) as exc:
        raise ValueError("amber and red thresholds must be numbers") from exc
    if not 0.0 <= amber_f < red_f <= 1.0:
        raise ValueError("thresholds must satisfy 0 ≤ amber < red ≤ 1")
    return {"amber": round(amber_f, 4), "red": round(red_f, 4)}


def score_to_decision(score: float, *, amber: float = DEFAULT_AMBER_THRESHOLD, red: float = DEFAULT_RED_THRESHOLD) -> str:
    value = float(score)
    if value >= red:
        return "red"
    if value >= amber:
        return "amber"
    return "green"
