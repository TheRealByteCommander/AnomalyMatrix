from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app import main as main_module
from app.event_bus import DomainEventBus
from app.main import app

client = TestClient(app)


def test_train_and_promote_patchcore_model(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    app.state.core_store = store
    main_module.event_bus = bus

    train = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "dataset_version": "v1", "sample_count": 8},
        headers={"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"},
    )
    assert train.status_code == 200
    model = train.json()["data"]
    model_id = model["model_id"]
    assert model["status"] == "candidate"
    assert model["metadata"]["embedding_count"] >= 3

    promote = client.post(
        f"/api/v1/models/{model_id}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert promote.status_code == 200
    promoted = promote.json()["data"]["model"]
    assert promoted["status"] == "active"

    events = bus.recent(limit=10)
    assert any(e["event_type"] == "ModelRetrained" for e in events)
