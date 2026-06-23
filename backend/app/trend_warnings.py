from __future__ import annotations

from .event_bus import DomainEventBus
from .trend_engine import evaluate_trend_warning


def enrich_trend_summary(base: dict, recent_items: list[dict], *, window: int = 20) -> dict:
    warning = evaluate_trend_warning(recent_items, window=window)
    return {**base, **warning}


def maybe_emit_trend_warning(
    event_bus: DomainEventBus,
    *,
    trend: dict,
    recipe_id: str,
    model_version: str,
) -> dict | None:
    if not trend.get("trend_warning"):
        return None

    severity = trend.get("trend_severity", "amber")
    for event in event_bus.recent(limit=15):
        if event.get("event_type") != "TrendWarningRaised":
            continue
        payload = event.get("payload") or {}
        if payload.get("severity") == severity and payload.get("recipe_id") == recipe_id:
            return None

    return event_bus.emit(
        "TrendWarningRaised",
        {
            "recipe_id": recipe_id,
            "model_version": model_version,
            "severity": severity,
            "reason": trend.get("trend_reason"),
            "window_avg_score": trend.get("window_avg_score"),
            "window_anomaly_rate_pct": trend.get("window_anomaly_rate_pct"),
            "window_size": trend.get("window_size"),
        },
    )
