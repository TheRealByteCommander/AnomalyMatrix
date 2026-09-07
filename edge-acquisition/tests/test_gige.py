"""GigE / GenICam unit tests — mocked GenTL/Harvesters/Aravis, no real cameras."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from camera_discover import discover_cameras, resolve_source
from camera_drivers import (
    GigECameraDriver,
    OpenCvCameraDriver,
    SyntheticCameraDriver,
    get_camera_driver,
)
from gige_backend import (
    GigEDevice,
    GigEUnavailableError,
    HarvestersBackend,
    find_cti_files,
    is_gige_driver,
    match_gige_device,
    select_backend,
    to_grayscale,
)


@pytest.fixture(autouse=True)
def _clean_camera_env(monkeypatch):
    monkeypatch.delenv("CAMERA_DRIVER", raising=False)
    monkeypatch.delenv("CAMERA_SOURCE", raising=False)
    monkeypatch.delenv("CAMERA_SOURCES_JSON", raising=False)
    monkeypatch.delenv("CAMERA_EXPOSURE_MS", raising=False)
    monkeypatch.delenv("CAMERA_GAIN_DB", raising=False)
    monkeypatch.delenv("CAMERA_TRIGGER", raising=False)
    monkeypatch.delenv("GIGE_BACKEND", raising=False)
    monkeypatch.delenv("GIGE_GENTL_CTI", raising=False)
    monkeypatch.delenv("GENICAM_GENTL64_PATH", raising=False)
    monkeypatch.delenv("SERVICE_AUTH_TOKEN", raising=False)


def test_is_gige_driver_aliases():
    assert is_gige_driver("gige")
    assert is_gige_driver("genicam")
    assert is_gige_driver("gigE")
    assert is_gige_driver("GigE Vision")
    assert is_gige_driver("GEV")
    assert not is_gige_driver("opencv")
    assert not is_gige_driver("synthetic")


def test_get_camera_driver_dispatch(monkeypatch):
    monkeypatch.setenv("CAMERA_DRIVER", "synthetic")
    assert isinstance(get_camera_driver(), SyntheticCameraDriver)
    monkeypatch.setenv("CAMERA_DRIVER", "opencv")
    assert isinstance(get_camera_driver(), OpenCvCameraDriver)
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    assert isinstance(get_camera_driver(), GigECameraDriver)
    monkeypatch.setenv("CAMERA_DRIVER", "genicam")
    assert isinstance(get_camera_driver(), GigECameraDriver)
    monkeypatch.setenv("CAMERA_DRIVER", "gigE")
    assert isinstance(get_camera_driver(), GigECameraDriver)


def test_synthetic_capture_unchanged():
    image, meta = SyntheticCameraDriver().capture(camera_id="cam-01", recipe_id="r")
    assert image.shape == (256, 256)
    assert image.dtype == np.uint8
    assert meta["driver"] == "synthetic"


def test_opencv_still_file(tmp_path, monkeypatch):
    import cv2

    path = tmp_path / "frame.png"
    cv2.imwrite(str(path), np.full((32, 48), 90, dtype=np.uint8))
    monkeypatch.setenv("CAMERA_SOURCE", str(path))
    image, meta = OpenCvCameraDriver().capture(camera_id="file-cam", recipe_id="r")
    assert image.shape == (32, 48)
    assert meta["driver"] == "opencv"
    assert meta["source"] == str(path)


def test_to_grayscale_mono_and_rgb_and_bayer():
    mono = np.arange(16, dtype=np.uint8).reshape(4, 4)
    assert to_grayscale(mono, "Mono8").shape == (4, 4)

    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb[:, :] = (10, 20, 30)
    gray = to_grayscale(rgb, "RGB8")
    assert gray.shape == (4, 4)
    assert gray.dtype == np.uint8

    bayer = np.zeros((8, 8), dtype=np.uint8)
    bayer[0::2, 0::2] = 200
    converted = to_grayscale(bayer, "BayerRG8")
    assert converted.shape == (8, 8)
    assert converted.dtype == np.uint8


def test_match_gige_device_serial_user_ip():
    devices = [
        GigEDevice(
            camera_id="CAM-FRONT",
            source="Basler-22345678",
            label="Basler acA1920",
            serial="22345678",
            user_id="CAM-FRONT",
            ip="192.168.1.10",
            gentl_id="Basler-22345678",
            model="acA1920-40gm",
        )
    ]
    assert match_gige_device(devices, "22345678").camera_id == "CAM-FRONT"
    assert match_gige_device(devices, "serial:22345678").serial == "22345678"
    assert match_gige_device(devices, "user:CAM-FRONT").user_id == "CAM-FRONT"
    assert match_gige_device(devices, "ip:192.168.1.10").ip == "192.168.1.10"
    assert match_gige_device(devices, "Basler-22345678").gentl_id == "Basler-22345678"
    assert match_gige_device(devices, "missing") is None


def test_find_cti_files(tmp_path, monkeypatch):
    producer = tmp_path / "FakeProducer.cti"
    producer.write_bytes(b"not-a-real-cti")
    monkeypatch.setenv("GIGE_GENTL_CTI", str(producer))
    monkeypatch.delenv("GENICAM_GENTL64_PATH", raising=False)
    found = find_cti_files()
    assert producer in found

    nested = tmp_path / "vendor" / "lib"
    nested.mkdir(parents=True)
    other = nested / "ProducerGEV.cti"
    other.write_bytes(b"x")
    monkeypatch.setenv("GIGE_GENTL_CTI", "")
    monkeypatch.setenv("GENICAM_GENTL64_PATH", str(tmp_path / "vendor"))
    found = find_cti_files()
    assert other in found


def test_select_backend_missing_producer(monkeypatch):
    monkeypatch.setenv("GIGE_BACKEND", "harvesters")
    monkeypatch.setattr("gige_backend.find_cti_files", lambda: [])
    with pytest.raises(GigEUnavailableError) as exc:
        select_backend()
    assert "cti" in str(exc.value).lower() or "GenTL" in str(exc.value)


def test_select_backend_aravis_missing(monkeypatch):
    import sys
    import types

    monkeypatch.setenv("GIGE_BACKEND", "aravis")
    fake_gi = types.ModuleType("gi")

    def _require_version(*_args, **_kwargs):
        raise ValueError("forced missing Aravis")

    fake_gi.require_version = _require_version
    monkeypatch.setitem(sys.modules, "gi", fake_gi)
    monkeypatch.setitem(sys.modules, "gi.repository", types.ModuleType("gi.repository"))
    with pytest.raises(GigEUnavailableError) as exc:
        select_backend()
    assert "Aravis" in str(exc.value) or "aravis" in str(exc.value).lower() or "GenTL" in str(exc.value)


class _FakeIA:
    def __init__(self, frame: np.ndarray):
        self.frame = frame
        self.remote_device = type("D", (), {"node_map": None})()
        self.stopped = False

    def start(self):
        return None

    def stop(self):
        self.stopped = True

    def destroy(self):
        return None

    def fetch(self, timeout=None):
        return _FakeBuffer(self.frame)


class _FakeBuffer:
    def __init__(self, frame: np.ndarray):
        h, w = frame.shape
        self.payload = type(
            "P",
            (),
            {
                "components": [
                    type(
                        "C",
                        (),
                        {
                            "height": h,
                            "width": w,
                            "data": frame.reshape(-1),
                            "data_format": "Mono8",
                        },
                    )()
                ]
            },
        )()

    def queue(self):
        return None


class _FakeInfo:
    id_ = "Fake-1001"
    serial_number = "1001"
    user_defined_name = "CAM-A"
    model = "FakeCam"
    vendor = "Acme"
    display_name = "Acme FakeCam"
    tl_type = "GEV"
    ip = "10.0.0.5"


class _FakeHarvester:
    def __init__(self):
        self.device_info_list = [_FakeInfo()]
        self.files: list[str] = []

    def add_file(self, path: str):
        self.files.append(path)

    def update(self):
        return None

    def reset(self):
        return None

    def create(self, spec=None):
        return _FakeIA(np.full((16, 20), 77, dtype=np.uint8))


def test_harvesters_discover_and_grab(tmp_path, monkeypatch):
    import sys
    import types

    cti = tmp_path / "fake.cti"
    cti.write_bytes(b"cti")
    monkeypatch.setenv("GIGE_GENTL_CTI", str(cti))
    monkeypatch.setenv("CAMERA_TRIGGER", "software")
    monkeypatch.setenv("CAMERA_EXPOSURE_MS", "12.5")
    monkeypatch.setenv("CAMERA_GAIN_DB", "3")

    core = types.ModuleType("harvesters.core")
    core.Harvester = _FakeHarvester
    pkg = types.ModuleType("harvesters")
    pkg.core = core
    monkeypatch.setitem(sys.modules, "harvesters", pkg)
    monkeypatch.setitem(sys.modules, "harvesters.core", core)

    import gige_backend as gb

    monkeypatch.setattr(gb.HarvestersBackend, "_harvester", lambda self: _FakeHarvester())

    backend = HarvestersBackend(cti_files=[cti])
    devices = backend.discover()
    assert len(devices) == 1
    assert devices[0].serial == "1001"
    assert devices[0].user_id == "CAM-A"
    assert devices[0].available is True

    frame, meta = backend.grab("1001")
    assert frame.shape == (16, 20)
    assert frame.dtype == np.uint8
    assert int(frame[0, 0]) == 77
    assert meta["driver"] == "gige"
    assert meta["backend"] == "harvesters"
    assert meta["trigger_mode"] == "software"
    assert meta["exposure_ms"] == 12.5
    assert meta["gain_db"] == 3.0


def test_discover_cameras_gige_mocked(monkeypatch):
    devices = [
        GigEDevice(
            camera_id="CAM-FRONT",
            source="Basler-1",
            label="Basler acA1920 (1)",
            available=True,
            index=0,
            model="acA1920-40gm",
            serial="1",
            ip="192.168.10.2",
            interface="GEV",
            backend="aravis",
        )
    ]
    info = {"backend": "aravis", "cti_files": [], "error": None}
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setattr("camera_discover.discover_gige_devices", lambda: (devices, info))
    payload = discover_cameras()
    assert payload["driver"] == "gige"
    assert payload["backend"] == "aravis"
    assert payload["cameras"][0]["serial"] == "1"
    assert payload["cameras"][0]["ip"] == "192.168.10.2"
    assert payload["cameras"][0]["available"] is True
    assert payload["max_selectable"] == 4


def test_discover_cameras_gige_unavailable(monkeypatch):
    info = {
        "backend": None,
        "cti_files": [],
        "error": "GigE/GenICam backend unavailable. Install a GenTL producer.",
    }
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setattr("camera_discover.discover_gige_devices", lambda: ([], info))
    payload = discover_cameras()
    assert payload["cameras"] == []
    assert "GenTL" in payload["error"]


def test_mapped_gige_sources(monkeypatch):
    devices = [
        GigEDevice(
            camera_id="1001",
            source="Fake-1001",
            label="Fake",
            serial="1001",
            available=True,
            backend="harvesters",
        )
    ]
    info = {"backend": "harvesters", "cti_files": ["/opt/gentl/x.cti"]}
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setenv("CAMERA_SOURCES_JSON", json.dumps({"cam-01": "1001", "cam-02": "missing"}))
    monkeypatch.setattr("camera_discover.discover_gige_devices", lambda: (devices, info))
    payload = discover_cameras()
    by_id = {c["camera_id"]: c for c in payload["cameras"]}
    assert by_id["cam-01"]["available"] is True
    assert by_id["cam-02"]["available"] is False


def test_resolve_source_gige(monkeypatch):
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setenv("CAMERA_SOURCE", "fallback-serial")
    assert resolve_source(camera_id="22345678") == "22345678"
    assert resolve_source(camera_id="CAM-FRONT") == "CAM-FRONT"
    assert resolve_source(camera_id="x", source="serial:9") == "serial:9"


def test_gige_capture_uses_backend(monkeypatch):
    gray = np.full((10, 12), 5, dtype=np.uint8)
    meta = {
        "driver": "gige",
        "source": "1001",
        "exposure_ms": 8.0,
        "gain_db": 1.5,
        "trigger_mode": "freerun",
        "backend": "aravis",
    }
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setattr("camera_drivers.grab_gige_frame", lambda source: (gray, dict(meta)))
    image, out = GigECameraDriver().capture(camera_id="1001", recipe_id="r")
    assert image.shape == (10, 12)
    assert out["trigger_mode"] == "freerun"
    assert out["backend"] == "aravis"


def test_gige_capture_clear_error_without_source(monkeypatch):
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setenv("CAMERA_SOURCE", "")
    with pytest.raises(GigEUnavailableError) as exc:
        GigECameraDriver().capture(camera_id="", recipe_id="r")
    assert "CAMERA_SOURCE" in str(exc.value)


def test_synthetic_discover_still_default():
    payload = discover_cameras()
    assert payload["driver"] == "synthetic"
    assert len(payload["cameras"]) == 4
    assert payload["cameras"][0]["camera_id"] == "cam-01"


def test_edge_http_gige_capture(monkeypatch):
    from fastapi.testclient import TestClient
    from service import app

    gray = np.full((8, 8), 11, dtype=np.uint8)
    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setattr(
        "camera_drivers.grab_gige_frame",
        lambda source: (
            gray,
            {
                "driver": "gige",
                "source": source,
                "exposure_ms": 4.0,
                "gain_db": 0.0,
                "trigger_mode": "software",
            },
        ),
    )
    client = TestClient(app)
    r = client.post("/capture", json={"camera_id": "1001"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["capture_driver"] == "gige"
    assert body["trigger_mode"] == "software"
    assert body["image_width"] == 8
    assert body["image_height"] == 8
    assert body["image_b64"]


def test_edge_http_gige_missing_backend(monkeypatch):
    from fastapi.testclient import TestClient
    from service import app

    monkeypatch.setenv("CAMERA_DRIVER", "gige")
    monkeypatch.setenv("CAMERA_SOURCE", "whatever")

    def _boom(source):
        raise GigEUnavailableError("No GenTL producer (.cti) found. " + source)

    monkeypatch.setattr("camera_drivers.grab_gige_frame", _boom)
    client = TestClient(app)
    r = client.post("/capture", json={"camera_id": "1001"})
    assert r.status_code == 503
    assert "GenTL" in r.json()["detail"]
