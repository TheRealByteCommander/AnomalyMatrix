from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.event_bus import DomainEventBus
from app.inference_provider import PatchCoreInferenceProvider, get_inference_provider
from app.main import app

client = TestClient(app)


def test_list_recipes_json_fallback(tmp_path):
    store = CoreStore(tmp_path)
    recipes = store.list_recipes()
    assert any(r["recipe_id"] == "recipe-default" for r in recipes)


def test_feedback_submit_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store
    app.state.event_bus = DomainEventBus(tmp_path)

    r = client.post(
        "/api/v1/feedback",
        json={"inspection_id": "insp-1", "verdict": "false_positive", "comment": "ok"},
        headers={"X-AMX-Role": "qa_lead", "X-AMX-User": "qa-1"},
    )
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["verdict"] == "false_positive"

    listing = client.get("/api/v1/feedback", headers={"X-AMX-Role": "qa_lead"})
    assert listing.status_code == 200
    assert listing.json()["data"]["count"] >= 1


def test_rbac_blocks_operator_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    monkeypatch.setenv("DATABASE_URL", "")
    app.state.core_store = CoreStore(tmp_path)
    app.state.event_bus = DomainEventBus(tmp_path)

    r = client.post(
        "/api/v1/feedback",
        json={"inspection_id": "x", "verdict": "needs_review"},
        headers={"X-AMX-Role": "operator"},
    )
    assert r.status_code == 403


def test_patchcore_provider_returns_bounded_score(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "patchcore")
    provider = get_inference_provider()
    assert isinstance(provider, PatchCoreInferenceProvider)
    out = provider.infer({"frame_id": "f-1", "camera_id": "cam-01", "recipe_id": "recipe-default"})
    assert 0.0 <= out.anomaly_score <= 1.0
    assert out.provider == "patchcore"
