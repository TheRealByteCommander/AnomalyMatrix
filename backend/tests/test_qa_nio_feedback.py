from pathlib import Path

from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.event_bus import DomainEventBus
from app import main as main_module
from app.main import app
from app.nio_store import count_nio_images, nio_images_dir
from app.repository import ResultRepository

client = TestClient(app)
QA = {"X-AMX-Role": "qa_lead", "X-AMX-User": "qa-1"}
ENGINEER = {"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"}
OPERATOR = {"X-AMX-Role": "operator", "X-AMX-User": "operator-1"}


def _bind(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub")
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    repo = ResultRepository(tmp_path)
    app.state.core_store = store
    app.state.event_bus = bus
    app.state.repo = repo
    main_module.core_store = store
    main_module.event_bus = bus
    main_module.repo = repo
    return store, repo


def test_confirm_anomaly_marks_inspection_nio_and_persists_sample(tmp_path, monkeypatch):
    store, repo = _bind(tmp_path, monkeypatch)
    run = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"})
    assert run.status_code == 200
    inspection = run.json()["data"]
    inspection_id = inspection["inspection_id"]
    auto_decision = inspection["decision"]
    assert auto_decision in {"green", "amber", "red"}
    heatmap = client.get(f"/api/v1/inspections/{inspection_id}/heatmap")
    assert heatmap.status_code == 200
    assert heatmap.headers["content-type"].startswith("image/png")
    assert inspection["heatmap"]["placeholder"] is False

    feedback = client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "verdict": "confirm_anomaly", "comment": "Riss bestätigt"},
        headers=QA,
    )
    assert feedback.status_code == 200
    body = feedback.json()["data"]
    assert body["verdict"] == "confirm_anomaly"
    assert body["decision"] == "red"
    assert body["decision_override"] == "red"
    assert body["nio_sample"]["inspection_id"] == inspection_id
    assert body["nio_count"] >= 1
    assert Path(body["nio_sample"]["path"]).exists()

    stored = repo.get(inspection_id)
    assert stored["decision"] == "red"
    assert stored["qa"]["verdict"] == "confirm_anomaly"
    assert stored["qa"]["override"] == "nio"
    assert stored["qa"]["auto_decision"] == auto_decision
    assert count_nio_images(tmp_path, "recipe-default") >= 1
    assert list(nio_images_dir(tmp_path, "recipe-default").glob("*.png"))

    recent = client.get("/api/v1/inspections/recent?limit=5").json()["data"]["items"]
    match = next(item for item in recent if item["inspection_id"] == inspection_id)
    assert match["decision"] == "red"

    listing = client.get("/api/v1/models?recipe_id=recipe-default", headers=ENGINEER).json()["data"]
    assert listing["nio_samples"]["count"] >= 1


def test_false_positive_does_not_mark_nio(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    inspection_id = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"}).json()["data"][
        "inspection_id"
    ]
    auto = client.get(f"/api/v1/inspections/{inspection_id}").json()["data"]["decision"]
    feedback = client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "verdict": "false_positive"},
        headers=QA,
    )
    assert feedback.status_code == 200
    body = feedback.json()["data"]
    assert body["decision_override"] is None
    assert body["nio_sample"] is None
    stored = client.get(f"/api/v1/inspections/{inspection_id}").json()["data"]
    assert stored["decision"] == auto
    assert stored["qa"]["verdict"] == "false_positive"
    assert stored["qa"]["override"] is None
    assert count_nio_images(tmp_path, "recipe-default") == 0


def test_needs_review_stays_pending_without_nio(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    inspection_id = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"}).json()["data"][
        "inspection_id"
    ]
    auto = client.get(f"/api/v1/inspections/{inspection_id}").json()["data"]["decision"]
    feedback = client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "verdict": "needs_review"},
        headers=QA,
    )
    assert feedback.status_code == 200
    stored = client.get(f"/api/v1/inspections/{inspection_id}").json()["data"]
    assert stored["decision"] == auto
    assert stored["qa"]["pending"] is True
    assert stored["qa"]["override"] is None
    assert count_nio_images(tmp_path, "recipe-default") == 0


def test_false_positive_after_confirm_restores_auto_decision(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    run = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"}).json()["data"]
    inspection_id = run["inspection_id"]
    auto = run["decision"]
    confirm = client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "verdict": "confirm_anomaly"},
        headers=QA,
    )
    assert confirm.status_code == 200
    assert confirm.json()["data"]["decision"] == "red"
    assert count_nio_images(tmp_path, "recipe-default") >= 1

    fp = client.post(
        "/api/v1/feedback",
        json={"inspection_id": inspection_id, "verdict": "false_positive"},
        headers=QA,
    )
    assert fp.status_code == 200
    stored = client.get(f"/api/v1/inspections/{inspection_id}").json()["data"]
    assert stored["decision"] == auto
    assert stored["qa"]["override"] is None
    assert stored["qa"]["verdict"] == "false_positive"
    assert count_nio_images(tmp_path, "recipe-default") == 0


def test_recipe_thresholds_adjustable_from_api(tmp_path, monkeypatch):
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    _bind(tmp_path, monkeypatch)
    blocked = client.put(
        "/api/v1/recipes/recipe-default/thresholds",
        json={"amber": 0.2, "red": 0.4},
        headers=OPERATOR,
    )
    assert blocked.status_code == 403

    updated = client.put(
        "/api/v1/recipes/recipe-default/thresholds",
        json={"amber": 0.2, "red": 0.4},
        headers=ENGINEER,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["decision_thresholds"] == {"amber": 0.2, "red": 0.4}

    recipes = client.get("/api/v1/recipes", headers=ENGINEER).json()["data"]["items"]
    match = next(r for r in recipes if r["recipe_id"] == "recipe-default")
    assert match["decision_thresholds"]["red"] == 0.4

    run = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"})
    assert run.status_code == 200
    result = run.json()["data"]
    assert result["decision_thresholds"] == {"amber": 0.2, "red": 0.4}
    score = float(result["inference"]["anomaly_score"])
    expected = "red" if score >= 0.4 else ("amber" if score >= 0.2 else "green")
    assert result["decision"] == expected

