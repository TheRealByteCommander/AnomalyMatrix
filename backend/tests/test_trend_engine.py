from app.trend_engine import evaluate_trend_warning


def _item(score: float, decision: str) -> dict:
    status = "anomaly" if decision != "green" else "ok"
    return {"decision": decision, "inference": {"anomaly_score": score, "status": status}}


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
