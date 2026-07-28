"""Multi-camera same-case inspection (1–4 views)."""

from fastapi.testclient import TestClient

from app.camera_station import CameraSelectionError, CameraStationStore
from app.main import app, camera_station


client = TestClient(app)


def test_camera_station_limits(tmp_path):
    store = CameraStationStore(tmp_path / "station.json")
    saved = store.save(camera_ids=["cam-01", "cam-02"], available_ids={"cam-01", "cam-02", "cam-03"})
    assert saved["camera_ids"] == ["cam-01", "cam-02"]
    try:
        store.save(camera_ids=[], available_ids={"cam-01"})
        raise AssertionError("expected empty selection to fail")
    except CameraSelectionError:
        pass
    try:
        store.save(
            camera_ids=["a", "b", "c", "d", "e"],
            available_ids={"a", "b", "c", "d", "e"},
        )
        raise AssertionError("expected >4 to fail")
    except CameraSelectionError:
        pass


def test_list_cameras_endpoint():
    r = client.get("/api/v1/cameras")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["min_selectable"] == 1
    assert body["data"]["max_selectable"] == 4
    assert isinstance(body["data"]["cameras"], list)
    assert len(body["data"]["cameras"]) >= 1


def test_save_selection_and_multi_view_run(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_ENFORCE", "false")
    camera_station.path = tmp_path / "station_cameras.json"
    camera_station.save(
        camera_ids=["cam-01", "cam-02"],
        sources={"cam-01": "synthetic:cam-01", "cam-02": "synthetic:cam-02"},
        available_ids={"cam-01", "cam-02", "cam-03", "cam-04"},
    )

    put = client.put(
        "/api/v1/cameras/selection",
        json={"camera_ids": ["cam-01", "cam-03"]},
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert put.status_code == 200, put.text
    assert put.json()["data"]["camera_ids"] == ["cam-01", "cam-03"]

    # No camera_id / camera_ids → use station selection
    run = client.post(
        "/api/v1/inspections/run",
        json={"recipe_id": "recipe-default"},
        headers={"X-AMX-Role": "operator", "X-AMX-User": "op-1"},
    )
    assert run.status_code == 200, run.text
    data = run.json()["data"]
    assert data["view_count"] == 2
    assert data["camera_ids"] == ["cam-01", "cam-03"]
    assert len(data["views"]) == 2
    assert data["decision"] in {"green", "amber", "red"}
    assert data["decision_policy"] == "worst_view"


def test_run_with_explicit_camera_ids():
    run = client.post(
        "/api/v1/inspections/run",
        json={"recipe_id": "recipe-default", "camera_ids": ["cam-01", "cam-02", "cam-04"]},
    )
    assert run.status_code == 200
    data = run.json()["data"]
    assert data["view_count"] == 3
    assert data["camera_ids"] == ["cam-01", "cam-02", "cam-04"]


def test_reject_more_than_four_cameras():
    run = client.post(
        "/api/v1/inspections/run",
        json={"camera_ids": ["cam-01", "cam-02", "cam-03", "cam-04", "cam-05"]},
    )
    assert run.status_code == 422
