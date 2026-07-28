from app.trend_engine import evaluate_multiview_trends, evaluate_trend_warning


def _item(score: float, decision: str, *, camera_id: str = "cam-01") -> dict:
    status = "anomaly" if decision != "green" else "ok"
    return {
        "decision": decision,
        "inference": {"anomaly_score": score, "status": status},
        "frame": {"camera_id": camera_id, "recipe_id": "recipe-default"},
        "camera_ids": [camera_id],
        "views": [
            {
                "camera_id": camera_id,
                "decision": decision,
                "inference": {"anomaly_score": score, "status": status},
                "frame": {"camera_id": camera_id, "recipe_id": "recipe-default"},
            }
        ],
    }


def test_trend_warning_requires_minimum_samples():
    out = evaluate_trend_warning([_item(0.9, "red")])
    assert out["trend_warning"] is False
    assert out["trend_severity"] == "green"


def test_trend_warning_elevated_avg_score():
    items = [_item(0.6, "amber"), _item(0.58, "green"), _item(0.57, "green")]
    out = evaluate_trend_warning(items)
    assert out["trend_warning"] is True
    assert out["trend_severity"] == "amber"
    assert "elevated_avg_score" in out["trend_reason"]


def test_trend_warning_consecutive_red():
    items = [_item(0.2, "green"), _item(0.91, "red"), _item(0.92, "red"), _item(0.93, "red")]
    out = evaluate_trend_warning(items)
    assert out["trend_warning"] is True
    assert out["trend_severity"] == "red"
    assert "consecutive_red" in out["trend_reason"]


def test_multiview_identifies_drifting_camera():
    items = []
    # Stable camera
    for score in (0.2, 0.21, 0.19, 0.22, 0.2, 0.21):
        items.append(_item(score, "green", camera_id="cam-stable"))
    # Drifting camera: baseline low, then elevated
    for score in (0.2, 0.22, 0.21, 0.7, 0.72, 0.75):
        items.append(
            {
                "decision": "amber" if score >= 0.55 else "green",
                "inference": {"anomaly_score": score, "status": "anomaly" if score >= 0.55 else "ok"},
                "frame": {"camera_id": "cam-drift", "recipe_id": "recipe-default"},
                "camera_ids": ["cam-stable", "cam-drift"],
                "views": [
                    {
                        "camera_id": "cam-stable",
                        "decision": "green",
                        "inference": {"anomaly_score": 0.2, "status": "ok"},
                        "frame": {"camera_id": "cam-stable"},
                    },
                    {
                        "camera_id": "cam-drift",
                        "decision": "amber" if score >= 0.55 else "green",
                        "inference": {"anomaly_score": score, "status": "anomaly" if score >= 0.55 else "ok"},
                        "frame": {"camera_id": "cam-drift"},
                    },
                ],
            }
        )

    out = evaluate_multiview_trends(items, window=20)
    assert out["by_camera"]
    cams = {c["camera_id"]: c for c in out["by_camera"]}
    assert "cam-drift" in cams
    assert cams["cam-drift"]["drift_warning"] is True
    assert out["drifting_camera_id"] == "cam-drift"
    assert "cam-drift" in (out.get("drifting_cameras") or [])
