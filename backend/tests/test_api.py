from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_envelope_and_request_id_roundtrip():
    r = client.get("/api/v1/health", headers={"X-Request-Id": "req-123"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["meta"]["requestId"] == "req-123"
    assert r.headers["X-Request-Id"] == "req-123"


def test_events_contracts_endpoint():
    r = client.get("/api/v1/contracts/events")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "InspectionCompleted" in body["data"]


def test_not_found_uses_error_envelope():
    r = client.get("/api/v1/unknown")
    assert r.status_code == 404
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "HTTP_ERROR"
    assert "requestId" in body["meta"]
