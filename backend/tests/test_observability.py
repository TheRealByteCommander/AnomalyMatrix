from fastapi.testclient import TestClient

from app.event_bus import DomainEventBus
from app.main import app

client = TestClient(app)


def test_run_inspection_emits_domain_event(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "license.json"))
    bus = DomainEventBus(tmp_path)
    monkeypatch.setattr("app.main.event_bus", bus)

    r = client.post("/api/v1/orchestrate/run-inspection", json={"camera_id": "cam-1", "recipe_id": "recipe-1"})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body.get("domain_event_id")

    events = bus.recent(limit=5)
    assert events
    assert events[0]["event_type"] == "InspectionCompleted"
    assert events[0]["payload"]["inspection_id"] == body["inspection_id"]


def test_observability_summary_endpoint():
    r = client.get("/api/v1/observability/summary")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "avg_score" in data
    assert "inspection_count" in data
    assert "metrics_source" in data


def test_events_recent_endpoint():
    r = client.get("/api/v1/events/recent")
    assert r.status_code == 200
    assert "items" in r.json()["data"]
