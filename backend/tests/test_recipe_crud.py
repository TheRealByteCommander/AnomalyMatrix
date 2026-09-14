from pathlib import Path

from fastapi.testclient import TestClient

from app import main as main_module
from app.core_store import PROTECTED_RECIPE_ID, CoreStore
from app.event_bus import DomainEventBus
from app.main import app
from app.repository import ResultRepository

client = TestClient(app)
ENGINEER = {"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"}
ADMIN = {"X-AMX-Role": "admin", "X-AMX-User": "admin-1"}
OPERATOR = {"X-AMX-Role": "operator", "X-AMX-User": "operator-1"}


def _bind(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    repo = ResultRepository(tmp_path)
    app.state.core_store = store
    app.state.event_bus = bus
    app.state.repo = repo
    main_module.core_store = store
    main_module.event_bus = bus
    main_module.repo = repo
    return store


def _create(recipe_id="recipe-seam-a", **extra):
    body = {
        "recipe_id": recipe_id,
        "name": extra.pop("name", "Seam A"),
        "recipe_version": extra.pop("recipe_version", "v1"),
        "active": extra.pop("active", False),
        "camera_profile": extra.pop("camera_profile", {"camera_id": "cam-02", "exposure_ms": 12}),
        "lighting_profile": extra.pop("lighting_profile", {"gain_db": 3}),
    }
    body.update(extra)
    return client.post("/api/v1/recipes", json=body, headers=ENGINEER)


def test_create_list_and_get_recipe(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    created = _create()
    assert created.status_code == 200, created.text
    body = created.json()["data"]
    assert body["recipe_id"] == "recipe-seam-a"
    assert body["name"] == "Seam A"
    assert body["camera_profile"]["camera_id"] == "cam-02"
    assert body["lighting_profile"]["gain_db"] == 3
    assert body["protected"] is False
    assert body["decision_thresholds"]["amber"] == 0.55

    listing = client.get("/api/v1/recipes", headers=OPERATOR)
    assert listing.status_code == 200
    ids = [item["recipe_id"] for item in listing.json()["data"]["items"]]
    assert PROTECTED_RECIPE_ID in ids
    assert "recipe-seam-a" in ids

    fetched = client.get("/api/v1/recipes/recipe-seam-a", headers=OPERATOR)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["name"] == "Seam A"


def test_update_recipe_fields_and_thresholds(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    assert _create().status_code == 200

    updated = client.put(
        "/api/v1/recipes/recipe-seam-a",
        json={
            "name": "Seam A revised",
            "recipe_version": "v2",
            "active": True,
            "camera_profile": {"camera_id": "cam-03", "exposure_ms": 8},
            "lighting_profile": {"gain_db": 1.5},
            "decision_thresholds": {"amber": 0.4, "red": 0.7},
        },
        headers=ENGINEER,
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()["data"]
    assert body["name"] == "Seam A revised"
    assert body["recipe_version"] == "v2"
    assert body["active"] is True
    assert body["status"] == "active"
    assert body["camera_profile"]["camera_id"] == "cam-03"
    assert body["decision_thresholds"] == {"amber": 0.4, "red": 0.7}

    default = client.get("/api/v1/recipes/recipe-default", headers=ENGINEER).json()["data"]
    assert default["active"] is False


def test_duplicate_and_invalid_recipe_id_rejected(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    assert _create().status_code == 200
    again = _create()
    assert again.status_code == 409

    bad = _create(recipe_id="../etc/passwd", name="Nope")
    assert bad.status_code in {400, 422}

    missing = client.get("/api/v1/recipes/does-not-exist", headers=ENGINEER)
    assert missing.status_code == 404


def test_delete_requires_double_confirmation(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    assert _create().status_code == 200

    no_body_fields = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": False, "confirm_recipe_id": ""},
        headers=ENGINEER,
    )
    assert no_body_fields.status_code == 400
    assert client.get("/api/v1/recipes/recipe-seam-a", headers=ENGINEER).status_code == 200

    mismatch = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": True, "confirm_recipe_id": "wrong-id"},
        headers=ENGINEER,
    )
    assert mismatch.status_code == 400

    ok = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": True, "confirm_recipe_id": "recipe-seam-a"},
        headers=ENGINEER,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["deleted"] is True
    assert client.get("/api/v1/recipes/recipe-seam-a", headers=ENGINEER).status_code == 404


def test_protected_default_recipe_cannot_be_deleted(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    blocked = client.request(
        "DELETE",
        f"/api/v1/recipes/{PROTECTED_RECIPE_ID}",
        json={"confirm": True, "confirm_recipe_id": PROTECTED_RECIPE_ID},
        headers=ADMIN,
    )
    assert blocked.status_code == 409
    assert client.get(f"/api/v1/recipes/{PROTECTED_RECIPE_ID}", headers=ADMIN).status_code == 200


def test_operator_can_read_but_not_mutate_recipes(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    listing = client.get("/api/v1/recipes", headers=OPERATOR)
    assert listing.status_code == 200

    created = client.post(
        "/api/v1/recipes",
        json={"recipe_id": "recipe-op", "name": "Operator try"},
        headers=OPERATOR,
    )
    assert created.status_code == 403

    updated = client.put(
        "/api/v1/recipes/recipe-default",
        json={"name": "Hijack"},
        headers=OPERATOR,
    )
    assert updated.status_code == 403

    deleted = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-default",
        json={"confirm": True, "confirm_recipe_id": "recipe-default"},
        headers=OPERATOR,
    )
    assert deleted.status_code == 403


def test_delete_blocked_when_active_or_candidate_model_bound(tmp_path, monkeypatch):
    store = _bind(tmp_path, monkeypatch)
    assert _create().status_code == 200
    store.register_model(
        {
            "model_id": "patchcore-bound",
            "name": "Bound",
            "model_version": "v1",
            "status": "candidate",
            "metadata": {"recipe_id": "recipe-seam-a"},
        }
    )
    blocked = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": True, "confirm_recipe_id": "recipe-seam-a"},
        headers=ENGINEER,
    )
    assert blocked.status_code == 409
    assert "candidate" in blocked.json()["error"]["message"] or "models" in blocked.json()["error"]["message"]


def test_delete_archives_training_and_nio_banks(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    assert _create().status_code == 200
    train = Path(tmp_path) / "training-images" / "recipe-seam-a"
    train.mkdir(parents=True)
    (train / "good.png").write_bytes(b"png")
    nio = Path(tmp_path) / "nio-images" / "recipe-seam-a"
    nio.mkdir(parents=True)
    (nio / "defect.png").write_bytes(b"png")

    ok = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": True, "confirm_recipe_id": "recipe-seam-a"},
        headers=ENGINEER,
    )
    assert ok.status_code == 200, ok.text
    assert not train.exists()
    assert not nio.exists()
    archived = list((Path(tmp_path) / "archived-recipes").rglob("*.png"))
    names = {p.name for p in archived}
    assert "good.png" in names
    assert "defect.png" in names
    moved = ok.json()["data"]["archived_assets"]["moved"]
    assert len(moved) == 2


def test_delete_active_recipe_activates_default(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    assert _create(active=True).status_code == 200
    default = client.get("/api/v1/recipes/recipe-default", headers=ENGINEER).json()["data"]
    assert default["active"] is False
    ok = client.request(
        "DELETE",
        "/api/v1/recipes/recipe-seam-a",
        json={"confirm": True, "confirm_recipe_id": "recipe-seam-a"},
        headers=ENGINEER,
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["activated_fallback"] == PROTECTED_RECIPE_ID
    default = client.get(f"/api/v1/recipes/{PROTECTED_RECIPE_ID}", headers=ENGINEER).json()["data"]
    assert default["active"] is True
