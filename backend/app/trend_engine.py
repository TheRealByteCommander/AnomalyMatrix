from __future__ import annotations

from typing import Any


def evaluate_trend_warning(items: list[dict], *, window: int = 20) -> dict[str, Any]:
    """Rolling trend analysis for dashboard and OPC-UA trend_warning node."""
    recent = items[-window:] if len(items) > window else list(items)
    if len(recent) < 3:
        return {
            "trend_warning": False,
            "trend_severity": "green",
            "trend_reason": None,
            "window_size": len(recent),
            "window_avg_score": 0.0,
            "window_anomaly_rate_pct": 0.0,
        }

    scores = [float(i.get("inference", {}).get("anomaly_score", 0.0)) for i in recent]
    decisions = [str(i.get("decision", "green")) for i in recent]
    avg = sum(scores) / len(scores)
    anomaly_rate = sum(1 for d in decisions if d != "green") / len(decisions)

    consecutive_red = 0
    for decision in reversed(decisions):
        if decision == "red":
            consecutive_red += 1
        else:
            break

    reasons: list[str] = []
    severity = "green"
    if consecutive_red >= 3:
        severity = "red"
        reasons.append("consecutive_red")
    elif avg >= 0.85:
        severity = "red"
        reasons.append("high_avg_score")
    elif anomaly_rate >= 0.4:
        severity = "amber"
        reasons.append("high_anomaly_rate")
    elif avg >= 0.55:
        severity = "amber"
        reasons.append("elevated_avg_score")

    return {
        "trend_warning": severity != "green",
        "trend_severity": severity,
        "trend_reason": ",".join(reasons) if reasons else None,
        "window_size": len(recent),
        "window_avg_score": round(avg, 4),
        "window_anomaly_rate_pct": round(anomaly_rate * 100, 1),
    }
