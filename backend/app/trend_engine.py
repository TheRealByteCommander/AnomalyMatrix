from __future__ import annotations

from typing import Any


_SEVERITY_RANK = {"green": 0, "amber": 1, "red": 2}


def _blank_trend(*, window_size: int = 0) -> dict[str, Any]:
    return {
        "trend_warning": False,
        "trend_severity": "green",
        "trend_reason": None,
        "window_size": window_size,
        "window_avg_score": 0.0,
        "window_anomaly_rate_pct": 0.0,
        "baseline_avg_score": 0.0,
        "score_delta": 0.0,
        "drift_score": 0.0,
    }


def _score_decision(item: dict) -> tuple[float, str]:
    score = float(item.get("inference", {}).get("anomaly_score", 0.0))
    decision = str(item.get("decision", "green"))
    return score, decision


def evaluate_trend_warning(items: list[dict], *, window: int = 20) -> dict[str, Any]:
    """Rolling trend analysis for a sequence of inspection (or view) samples."""
    recent = items[-window:] if len(items) > window else list(items)
    if len(recent) < 3:
        return _blank_trend(window_size=len(recent))

    scores = [_score_decision(i)[0] for i in recent]
    decisions = [_score_decision(i)[1] for i in recent]
    avg = sum(scores) / len(scores)
    anomaly_rate = sum(1 for d in decisions if d != "green") / len(decisions)

    # Baseline = earlier half of the window (or previous samples outside recent half)
    half = max(1, len(recent) // 2)
    baseline_scores = scores[:half] if len(scores) >= 4 else scores[:1]
    baseline_avg = sum(baseline_scores) / len(baseline_scores)
    score_delta = avg - baseline_avg
    # drift_score: relative elevation vs baseline (0 = no drift)
    drift_score = round(max(0.0, score_delta) / max(0.05, 1.0 - baseline_avg), 4)

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
    elif score_delta >= 0.2 and avg >= 0.55:
        severity = "red" if score_delta >= 0.35 else "amber"
        reasons.append("camera_drift_above_baseline")
    elif anomaly_rate >= 0.4:
        severity = "amber"
        reasons.append("high_anomaly_rate")
    elif avg >= 0.55:
        severity = "amber"
        reasons.append("elevated_avg_score")
    elif score_delta >= 0.12:
        severity = "amber"
        reasons.append("rising_vs_baseline")

    return {
        "trend_warning": severity != "green",
        "trend_severity": severity,
        "trend_reason": ",".join(reasons) if reasons else None,
        "window_size": len(recent),
        "window_avg_score": round(avg, 4),
        "window_anomaly_rate_pct": round(anomaly_rate * 100, 1),
        "baseline_avg_score": round(baseline_avg, 4),
        "score_delta": round(score_delta, 4),
        "drift_score": drift_score,
    }


def _iter_view_samples(items: list[dict]) -> list[dict]:
    """Expand case inspections into per-camera view samples for drift analysis."""
    samples: list[dict] = []
    for item in items:
        views = item.get("views")
        if isinstance(views, list) and views:
            for view in views:
                samples.append(
                    {
                        "camera_id": view.get("camera_id") or (view.get("frame") or {}).get("camera_id"),
                        "recipe_id": (view.get("frame") or {}).get("recipe_id")
                        or (item.get("frame") or {}).get("recipe_id"),
                        "decision": view.get("decision", item.get("decision", "green")),
                        "inference": view.get("inference") or item.get("inference") or {},
                        "inspection_id": item.get("inspection_id"),
                        "captured_at": (view.get("frame") or {}).get("captured_at"),
                    }
                )
        else:
            frame = item.get("frame") or {}
            samples.append(
                {
                    "camera_id": frame.get("camera_id", "unknown"),
                    "recipe_id": frame.get("recipe_id"),
                    "decision": item.get("decision", "green"),
                    "inference": item.get("inference") or {},
                    "inspection_id": item.get("inspection_id"),
                    "captured_at": frame.get("captured_at"),
                }
            )
    return samples


def evaluate_multiview_trends(items: list[dict], *, window: int = 20) -> dict[str, Any]:
    """Case-level trend plus concrete per-camera drift breakdown."""
    case_trend = evaluate_trend_warning(items, window=window)
    samples = _iter_view_samples(items)

    by_camera_map: dict[str, list[dict]] = {}
    for sample in samples:
        cam = str(sample.get("camera_id") or "unknown")
        by_camera_map.setdefault(cam, []).append(sample)

    by_camera: list[dict[str, Any]] = []
    for camera_id, cam_items in sorted(by_camera_map.items()):
        cam_trend = evaluate_trend_warning(cam_items, window=window)
        last = cam_items[-1] if cam_items else {}
        by_camera.append(
            {
                "camera_id": camera_id,
                "sample_count": len(cam_items),
                "last_inspection_id": last.get("inspection_id"),
                **cam_trend,
                "drift_warning": bool(cam_trend.get("trend_warning")),
                "severity": cam_trend.get("trend_severity", "green"),
                "reason": cam_trend.get("trend_reason"),
            }
        )

    drifting = [c for c in by_camera if c.get("drift_warning")]
    drifting.sort(
        key=lambda c: (
            _SEVERITY_RANK.get(str(c.get("severity", "green")), 0),
            float(c.get("drift_score") or 0.0),
            float(c.get("score_delta") or 0.0),
        ),
        reverse=True,
    )
    primary = drifting[0] if drifting else None

    # Elevate case warning if any camera drifts harder than case-level signal
    if primary and _SEVERITY_RANK.get(primary["severity"], 0) > _SEVERITY_RANK.get(
        case_trend.get("trend_severity", "green"), 0
    ):
        case_trend = {
            **case_trend,
            "trend_warning": True,
            "trend_severity": primary["severity"],
            "trend_reason": f"camera_drift:{primary['camera_id']}:{primary.get('reason') or 'elevated'}",
        }
    elif primary and not case_trend.get("trend_warning"):
        case_trend = {
            **case_trend,
            "trend_warning": True,
            "trend_severity": primary["severity"],
            "trend_reason": f"camera_drift:{primary['camera_id']}:{primary.get('reason') or 'elevated'}",
        }

    return {
        **case_trend,
        "by_camera": by_camera,
        "drifting_camera_id": primary["camera_id"] if primary else None,
        "drifting_cameras": [c["camera_id"] for c in drifting],
        "camera_count": len(by_camera),
        "view_sample_count": len(samples),
    }
