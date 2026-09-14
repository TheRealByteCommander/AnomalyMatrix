from pathlib import Path

from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app import main as main_module
from app.event_bus import DomainEventBus
from app.main import app
from app.patchcore_memory import active_memory_bank_path, load_memory_bank

client = TestClient(app)

ENGINEER = {"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"}
ADMIN = {"X-AMX-Role": "admin", "X-AMX-User": "admin-1"}
OPERATOR = {"X-AMX-Role": "operator", "X-AMX-User": "operator-1"}


def _bind_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    app.state.core_store = store
    main_module.event_bus = bus
    return store, bus


def test_train_and_promote_patchcore_model(tmp_path, monkeypatch):
    store, bus = _bind_store(tmp_path, monkeypatch)

    train = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "dataset_version": "v1", "sample_count": 8},
        headers=ENGINEER,
    )
    assert train.status_code == 200
    model = train.json()["data"]
    model_id = model["model_id"]
    assert model["status"] == "candidate"
    assert model["metadata"]["embedding_count"] >= 3
    artifact = Path(model["metadata"]["artifact_uri"])
    assert artifact.exists()
    # Candidate training must not hijack the live bank.
    active_link = active_memory_bank_path(tmp_path)
    assert not active_link.exists() or active_link.resolve() != artifact.resolve()

    listing = client.get("/api/v1/models", headers=ENGINEER)
    assert listing.status_code == 200
    listed = listing.json()["data"]
    assert listed["count"] >= 2
    match = next(m for m in listed["items"] if m["model_id"] == model_id)
    assert match["metadata"]["data_source"]
    assert match.get("created_at")

    promote = client.post(
        f"/api/v1/models/{model_id}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )
    assert promote.status_code == 200
    promoted = promote.json()["data"]["model"]
    assert promoted["status"] == "active"
    assert active_link.exists()
    bank, meta = load_memory_bank(active_link)
    assert bank.shape[0] >= 3
    assert meta.get("recipe_id") == "recipe-default"

    events = bus.recent(limit=10)
    assert any(e["event_type"] == "ModelRetrained" for e in events)


def test_training_history_activate_reuses_artifact(tmp_path, monkeypatch):
    _bind_store(tmp_path, monkeypatch)

    first = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 8},
        headers=ENGINEER,
    ).json()["data"]
    second = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 10},
        headers=ENGINEER,
    ).json()["data"]

    first_artifact = Path(first["metadata"]["artifact_uri"])
    second_artifact = Path(second["metadata"]["artifact_uri"])
    assert first_artifact.exists()
    assert second_artifact.exists()
    assert first_artifact != second_artifact

    client.post(
        f"/api/v1/models/{first['model_id']}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )
    client.post(
        f"/api/v1/models/{second['model_id']}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )

    activate = client.post(f"/api/v1/models/{first['model_id']}/activate", headers=ADMIN)
    assert activate.status_code == 200
    body = activate.json()["data"]
    assert body["model"]["status"] == "active"
    assert body["previous"]["model_id"] == second["model_id"]

    listing = client.get("/api/v1/models", headers=ENGINEER).json()["data"]
    by_id = {m["model_id"]: m for m in listing["items"]}
    assert by_id[first["model_id"]]["status"] == "active"
    assert by_id[second["model_id"]]["status"] == "archived"
    assert first_artifact.exists()
    assert second_artifact.exists()
    assert listing["memory_bank"]["loaded"] is True
    assert Path(listing["memory_bank"]["path"]).exists()


def test_capture_training_samples_and_local_train(tmp_path, monkeypatch):
    _bind_store(tmp_path, monkeypatch)

    captured = client.post(
        "/api/v1/models/training-samples",
        json={"recipe_id": "recipe-default", "count": 4, "camera_id": "cam-01"},
        headers=ENGINEER,
    )
    assert captured.status_code == 200
    data = captured.json()["data"]
    assert data["saved"] == 4
    assert data["count"] >= 4
    folder = tmp_path / "training-images" / "recipe-default"
    assert len(list(folder.glob("*.png"))) == 4

    trained = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 4},
        headers=ENGINEER,
    )
    assert trained.status_code == 200
    assert trained.json()["data"]["metadata"]["data_source"] == "local_files"


def test_operator_cannot_train_or_promote(tmp_path, monkeypatch):
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    _bind_store(tmp_path, monkeypatch)

    train = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 8},
        headers=OPERATOR,
    )
    assert train.status_code == 403

    listing = client.get("/api/v1/models", headers=OPERATOR)
    assert listing.status_code == 200


def test_rollback_restores_previous_bank(tmp_path, monkeypatch):
    _bind_store(tmp_path, monkeypatch)
    first = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 8},
        headers=ENGINEER,
    ).json()["data"]
    second = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 8},
        headers=ENGINEER,
    ).json()["data"]
    client.post(
        f"/api/v1/models/{first['model_id']}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )
    client.post(
        f"/api/v1/models/{second['model_id']}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )
    rolled = client.post("/api/v1/models/rollback", headers=ADMIN)
    assert rolled.status_code == 200
    restored = rolled.json()["data"]["restored_model"]
    assert restored["model_id"] == first["model_id"]
    active_link = active_memory_bank_path(tmp_path)
    assert active_link.exists()
    _, meta = load_memory_bank(active_link)
    assert meta.get("model_version") == first["model_version"]


def test_promote_rejects_small_sample_count_with_readable_error(tmp_path, monkeypatch):
    _bind_store(tmp_path, monkeypatch)
    trained = client.post(
        "/api/v1/models/train",
        json={"recipe_id": "recipe-default", "sample_count": 4},
        headers=ENGINEER,
    ).json()["data"]
    promote = client.post(
        f"/api/v1/models/{trained['model_id']}/promote",
        json={"baseline_score": 0.4, "candidate_score": 0.3},
        headers=ADMIN,
    )
    assert promote.status_code == 409
    message = promote.json()["error"]["message"]
    assert "insufficient_samples" in message
    activate = client.post(f"/api/v1/models/{trained['model_id']}/activate", headers=ADMIN)
    assert activate.status_code == 200
    assert activate.json()["data"]["model"]["status"] == "active"
