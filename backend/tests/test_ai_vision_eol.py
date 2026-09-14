"""AI Vision EOL: MQTT trigger, EPC binding, retention, station profile."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.event_bus import DomainEventBus
from app import main as main_module
from app.main import app
from app.mqtt_trigger import parse_mqtt_payload
from app.repository import ResultRepository
from app.retention import apply_local_retention
from app.station_vision import StationVisionStore

client = TestClient(app)
ENGINEER = {"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"}
OPERATOR = {"X-AMX-Role": "operator", "X-AMX-User": "operator-1"}
QA = {"X-AMX-Role": "qa_lead", "X-AMX-User": "qa-1"}


def _bind(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub")
    monkeypatch.setenv("LICENSE_ENFORCE", "false")
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    repo = ResultRepository(tmp_path)
    app.state.core_store = store
    app.state.event_bus = bus
    app.state.repo = repo
    main_module.core_store = store
    main_module.event_bus = bus
    main_module.repo = repo
    main_module.vision_store = StationVisionStore(tmp_path / "station_vision_profile.json")
    app.state.vision_store = main_module.vision_store
    from app.retention import RetentionStore
    from app.watchdog import CaptureWatchdog

    main_module.retention_store = RetentionStore(tmp_path / "retention_policy.json")
    app.state.retention_store = main_module.retention_store
    main_module.capture_watchdog = CaptureWatchdog(tmp_path / "capture_watchdog.json")
    app.state.capture_watchdog = main_module.capture_watchdog
    main_module._data_root = tmp_path
    store.data_root = tmp_path
    return store, repo


def test_parse_mqtt_payload_aliases():
    parsed = parse_mqtt_payload(
        {"trigger": "start", "EPC": "urn:epc:id:sgtin:0614141.107346.2017", "recipe": "recipe-default"}
    )
    assert parsed["action"] == "inspect"
    assert parsed["epc"].startswith("urn:epc:")
    assert parsed["recipe_id"] == "recipe-default"


def test_mqtt_trigger_starts_inspection_with_epc(tmp_path, monkeypatch):
    store, repo = _bind(tmp_path, monkeypatch)
    r = client.post(
        "/api/v1/triggers/mqtt",
        json={"payload": {"action": "inspect", "epc": "EPC-1001", "process_id": "PROC-9"}},
        headers=OPERATOR,
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["parsed"]["epc"] == "EPC-1001"
    result = body["result"]
    if "inspection_id" not in result:
        result = result.get("result") or result
    assert result["epc"] == "EPC-1001"
    assert result["process_id"] == "PROC-9"
    assert result["epc_binding"]["unique_key"] == "EPC-1001"
    assert result["trigger_source"] == "mqtt"
    stored = repo.get(result["inspection_id"])
    assert stored["epc"] == "EPC-1001"
    assert any(Path(tmp_path).joinpath("captures").rglob("*.json")) or stored.get("capture_set")


def test_epc_on_api_inspection_and_sidecar(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    run = client.post(
        "/api/v1/inspections/run",
        json={"recipe_id": "recipe-default", "epc": "EPC-HMI-7", "trigger_source": "hmi"},
        headers=OPERATOR,
    )
    assert run.status_code == 200, run.text
    data = run.json()["data"]
    assert data["epc"] == "EPC-HMI-7"
    assert data["capture_set"]["epc_binding"]["epc"] == "EPC-HMI-7"
    sidecars = list((tmp_path / "captures").rglob("*.json"))
    assert sidecars
    import json

    meta = json.loads(sidecars[0].read_text(encoding="utf-8"))
    assert meta["epc"] == "EPC-HMI-7" or meta.get("schema") == "ImageAsset"


def test_retention_job_archives_expired_and_honors_legal_hold(tmp_path):
    captures = tmp_path / "captures"
    old = captures / "eol" / "old.png"
    hold = captures / "eol" / "hold.png"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_bytes(b"old-image")
    hold.write_bytes(b"hold-image")
    hold.with_suffix(".json").write_text('{"legal_hold": true}', encoding="utf-8")
    import os
    import time

    past = time.time() - 10 * 86400
    os.utime(old, (past, past))
    os.utime(hold, (past, past))
    policy = {
        "ttl_days": 1,
        "archive_prefix": "eol/",
        "delete_after_archive": True,
        "enabled": True,
    }
    result = apply_local_retention(root=captures, policy=policy)
    assert result["archived"] >= 1
    assert result["legal_hold"] >= 1
    assert not old.exists()
    assert hold.exists()
    archived = list((captures / "archive").rglob("old.png"))
    assert archived


def test_station_vision_export_import_clone(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    got = client.get("/api/v1/station/vision-profile", headers=ENGINEER)
    assert got.status_code == 200
    profile = got.json()["data"]
    profile["cameras"][0]["role"] = "bottom"
    profile["cameras"][0]["lens_notes"] = "8mm C-mount"
    profile["checklist"]["corners_visible"] = True
    saved = client.put("/api/v1/station/vision-profile", json=profile, headers=ENGINEER)
    assert saved.status_code == 200, saved.text
    assert saved.json()["data"]["cameras"][0]["role"] == "bottom"
    exported = client.get("/api/v1/station/vision-profile/export?format=yaml", headers=ENGINEER)
    assert exported.status_code == 200
    assert "station_id:" in exported.text
    cloned = client.post(
        "/api/v1/station/vision-profile/clone",
        json={"station_id": "eol-line-2", "name": "Line 2"},
        headers=ENGINEER,
    )
    assert cloned.status_code == 200
    assert cloned.json()["data"]["station_id"] == "eol-line-2"
    rec = client.get("/api/v1/station/recommendations", headers=ENGINEER)
    assert rec.status_code == 200
    assert rec.json()["data"]["items"]


def test_retention_policy_endpoint_and_run(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    put = client.put(
        "/api/v1/storage/retention",
        json={"ttl_days": 30, "archive_bucket": "archive-images", "legal_hold_default": False},
        headers=ENGINEER,
    )
    assert put.status_code == 200
    assert put.json()["data"]["ttl_days"] == 30
    run = client.post("/api/v1/storage/retention/run", headers=ENGINEER)
    assert run.status_code == 200
    assert "local" in run.json()["data"]


def test_watchdog_and_self_test(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    client.post("/api/v1/inspections/run", json={"epc": "EPC-W"}, headers=OPERATOR)
    wd = client.get("/api/v1/system/watchdog", headers=OPERATOR)
    assert wd.status_code == 200
    assert wd.json()["data"]["capture_count"] >= 1
    st = client.post("/api/v1/system/self-test", headers=OPERATOR)
    assert st.status_code == 200
    assert "checks" in st.json()["data"]


def test_storage_stats_after_capture(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    client.post("/api/v1/inspections/run", json={"epc": "EPC-S"}, headers=OPERATOR)
    stats = client.get("/api/v1/storage/stats", headers=ENGINEER)
    assert stats.status_code == 200
    data = stats.json()["data"]
    assert data["object_count"] >= 1
    assert data["total_bytes"] >= 1


def test_eol_contracts_listed(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch)
    r = client.get("/api/v1/contracts/eol", headers=ENGINEER)
    assert r.status_code == 200
    schemas = r.json()["data"]["schemas"]
    assert "ImageAsset" in schemas
    assert "EpcBinding" in schemas
    assert "StationVisionProfile" in schemas


def test_max_cameras_env_allows_five(tmp_path, monkeypatch):
    monkeypatch.setenv("AMX_MAX_CAMERAS", "8")
    from app.camera_limits import max_cameras
    from app.camera_station import CameraStationStore

    assert max_cameras() == 8
    store = CameraStationStore(tmp_path / "station.json")
    saved = store.save(
        camera_ids=["a", "b", "c", "d", "e"],
        available_ids={"a", "b", "c", "d", "e"},
    )
    assert saved["camera_ids"] == ["a", "b", "c", "d", "e"]
