from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.event_bus import DomainEventBus
from app import main as main_module
from app.main import app

client = TestClient(app)


def test_e2e_capture_infer_run_feedback(tmp_path, monkeypatch):
    """Vertical slice: edge capture → AI infer → orchestrated run → QA feedback."""
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub")
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    app.state.core_store = store
    app.state.event_bus = bus
    main_module.event_bus = bus

    capture = client.post(
        "/api/v1/edge/capture",
        json={"camera_id": "cam-e2e", "recipe_id": "recipe-default"},
    )
    assert capture.status_code == 200
    frame = capture.json()["data"]
    assert frame["camera_id"] == "cam-e2e"

    infer = client.post(
        "/api/v1/ai/infer",
        json={
            "frame_id": frame["frame_id"],
            "camera_id": frame["camera_id"],
            "recipe_id": frame["recipe_id"],
        },
    )
    assert infer.status_code == 200
    inference = infer.json()["data"]
    assert 0.0 <= inference["anomaly_score"] <= 1.0

    run = client.post(
        "/api/v1/inspections/run",
        json={"camera_id": "cam-e2e", "recipe_id": "recipe-default"},
    )
    assert run.status_code == 200
    result = run.json()["data"]
    inspection_id = result["inspection_id"]
    assert result["frame"]["recipe_id"] == "recipe-default"
    assert "opcua_publish" in result

    feedback = client.post(
        "/api/v1/feedback",
        json={
            "inspection_id": inspection_id,
            "verdict": "needs_review",
            "comment": "e2e validation",
        },
        headers={"X-AMX-Role": "qa_lead", "X-AMX-User": "qa-e2e"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["data"]["verdict"] == "needs_review"

    recent = client.get("/api/v1/inspections/recent?limit=5")
    assert recent.status_code == 200
    ids = [item["inspection_id"] for item in recent.json()["data"]["items"]]
    assert inspection_id in ids

    events = client.get("/api/v1/events/recent?limit=20")
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()["data"]["items"]}
    assert "InspectionCompleted" in event_types
    assert "FeedbackSubmitted" in event_types

    trend = client.get("/api/v1/results/trend-summary")
    assert trend.status_code == 200
    trend_body = trend.json()["data"]
    assert "trend_warning" in trend_body
    assert "trend_severity" in trend_body
