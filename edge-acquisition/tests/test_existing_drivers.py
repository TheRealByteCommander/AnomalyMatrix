"""Regression tests for synthetic / OpenCV drivers."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from camera_discover import discover_cameras
from camera_drivers import OpenCvCameraDriver, get_camera_driver


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("CAMERA_DRIVER", raising=False)
    monkeypatch.delenv("CAMERA_SOURCE", raising=False)
    monkeypatch.delenv("CAMERA_SOURCES_JSON", raising=False)
    monkeypatch.delenv("CAMERA_FOURCC", raising=False)
    monkeypatch.delenv("CAMERA_WIDTH", raising=False)
    monkeypatch.delenv("CAMERA_HEIGHT", raising=False)
    monkeypatch.delenv("CAMERA_FPS", raising=False)
    monkeypatch.delenv("SERVICE_AUTH_TOKEN", raising=False)


def test_http_synthetic_capture():
    from service import app

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    cams = client.get("/cameras")
    assert cams.status_code == 200
    assert cams.json()["driver"] == "synthetic"
    cap = client.post("/capture", json={"camera_id": "cam-01", "recipe_id": "recipe-default"})
    assert cap.status_code == 200
    body = cap.json()
    assert body["capture_driver"] == "synthetic"
    assert body["image_width"] == 256
    assert body["image_b64"]


def test_opencv_driver_missing_source(monkeypatch):
    monkeypatch.setenv("CAMERA_DRIVER", "opencv")
    monkeypatch.setenv("CAMERA_SOURCE", "/no/such/camera.png")
    with pytest.raises(RuntimeError, match="not found"):
        OpenCvCameraDriver().capture(camera_id="x", recipe_id="r")


def test_opencv_mapped_json(monkeypatch, tmp_path):
    import cv2

    img = tmp_path / "a.png"
    cv2.imwrite(str(img), np.zeros((10, 10), dtype=np.uint8))
    monkeypatch.setenv("CAMERA_DRIVER", "opencv")
    monkeypatch.setenv("CAMERA_SOURCES_JSON", '{"cam-file":"%s"}' % img)
    payload = discover_cameras()
    assert payload["driver"] == "opencv"
    assert payload["cameras"][0]["camera_id"] == "cam-file"
    assert payload["cameras"][0]["available"] is True
    driver = get_camera_driver()
    frame, meta = driver.capture(camera_id="cam-file", recipe_id="r")
    assert frame.shape == (10, 10)
    assert meta["driver"] == "opencv"
    assert "fourcc" not in meta
    assert "fps" not in meta


class _FakeVideoCapture:
    instances: list["_FakeVideoCapture"] = []
    negotiated: dict[int, float | int] | None = None

    def __init__(self, device, *args, **kwargs):
        self.device = device
        self.props: dict[int, float | int] = {}
        self.sets: list[tuple[int, float | int]] = []
        self.read_calls = 0
        self.released = False
        type(self).instances.append(self)

    def set(self, prop, value):
        self.sets.append((int(prop), value))
        self.props[int(prop)] = value
        return True

    def get(self, prop):
        key = int(prop)
        if self.negotiated is not None and key in self.negotiated:
            return self.negotiated[key]
        return self.props.get(key, 0)

    def read(self):
        import cv2

        self.read_calls += 1
        width = int(self.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        height = int(self.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        return True, np.zeros((height, width, 3), dtype=np.uint8)

    def release(self):
        self.released = True

    def isOpened(self):
        return not self.released


def _patch_videocapture(monkeypatch):
    import cv2

    _FakeVideoCapture.instances = []
    _FakeVideoCapture.negotiated = None
    monkeypatch.setattr(cv2, "VideoCapture", _FakeVideoCapture)
    return cv2


def test_opencv_live_sets_default_mjpg_4k_before_read(monkeypatch):
    cv2 = _patch_videocapture(monkeypatch)
    monkeypatch.setenv("CAMERA_SOURCE", "0")

    frame, meta = OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    cap = _FakeVideoCapture.instances[-1]

    assert cap.device == 0
    assert cap.read_calls == 1
    assert cap.released is True
    assert [prop for prop, _ in cap.sets] == [
        cv2.CAP_PROP_FOURCC,
        cv2.CAP_PROP_FRAME_WIDTH,
        cv2.CAP_PROP_FRAME_HEIGHT,
        cv2.CAP_PROP_FPS,
    ]
    by_prop = dict(cap.sets)
    assert by_prop[cv2.CAP_PROP_FOURCC] == cv2.VideoWriter_fourcc(*"MJPG")
    assert by_prop[cv2.CAP_PROP_FRAME_WIDTH] == 3840.0
    assert by_prop[cv2.CAP_PROP_FRAME_HEIGHT] == 2160.0
    assert by_prop[cv2.CAP_PROP_FPS] == 30.0
    assert frame.shape == (2160, 3840)
    assert meta["width"] == 3840
    assert meta["height"] == 2160
    assert meta["fps"] == 30.0
    assert meta["fourcc"] == "MJPG"


def test_opencv_live_applies_env_overrides(monkeypatch):
    cv2 = _patch_videocapture(monkeypatch)
    monkeypatch.setenv("CAMERA_SOURCE", "2")
    monkeypatch.setenv("CAMERA_FOURCC", "YUYV")
    monkeypatch.setenv("CAMERA_WIDTH", "1920")
    monkeypatch.setenv("CAMERA_HEIGHT", "1080")
    monkeypatch.setenv("CAMERA_FPS", "15")

    _frame, meta = OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    by_prop = dict(_FakeVideoCapture.instances[-1].sets)
    assert by_prop[cv2.CAP_PROP_FOURCC] == cv2.VideoWriter_fourcc(*"YUYV")
    assert by_prop[cv2.CAP_PROP_FRAME_WIDTH] == 1920.0
    assert by_prop[cv2.CAP_PROP_FRAME_HEIGHT] == 1080.0
    assert by_prop[cv2.CAP_PROP_FPS] == 15.0
    assert meta["width"] == 1920
    assert meta["height"] == 1080
    assert meta["fps"] == 15.0
    assert meta["fourcc"] == "YUYV"


def test_opencv_live_meta_uses_negotiated_get_values(monkeypatch):
    cv2 = _patch_videocapture(monkeypatch)
    monkeypatch.setenv("CAMERA_SOURCE", "0")
    _FakeVideoCapture.negotiated = {
        cv2.CAP_PROP_FRAME_WIDTH: 1920,
        cv2.CAP_PROP_FRAME_HEIGHT: 1080,
        cv2.CAP_PROP_FPS: 15.0,
        cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc(*"YUYV"),
    }

    frame, meta = OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    cap = _FakeVideoCapture.instances[-1]
    assert dict(cap.sets)[cv2.CAP_PROP_FRAME_WIDTH] == 3840.0
    assert frame.shape == (1080, 1920)
    assert meta["width"] == 1920
    assert meta["height"] == 1080
    assert meta["fps"] == 15.0
    assert meta["fourcc"] == "YUYV"


def test_opencv_live_invalid_env_falls_back_to_defaults(monkeypatch):
    cv2 = _patch_videocapture(monkeypatch)
    monkeypatch.setenv("CAMERA_SOURCE", "0")
    monkeypatch.setenv("CAMERA_FOURCC", "")
    monkeypatch.setenv("CAMERA_WIDTH", "nope")
    monkeypatch.setenv("CAMERA_HEIGHT", "-1")
    monkeypatch.setenv("CAMERA_FPS", "0")

    _frame, meta = OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    by_prop = dict(_FakeVideoCapture.instances[-1].sets)
    assert by_prop[cv2.CAP_PROP_FOURCC] == cv2.VideoWriter_fourcc(*"MJPG")
    assert by_prop[cv2.CAP_PROP_FRAME_WIDTH] == 3840.0
    assert by_prop[cv2.CAP_PROP_FRAME_HEIGHT] == 2160.0
    assert by_prop[cv2.CAP_PROP_FPS] == 30.0
    assert meta["fourcc"] == "MJPG"


def test_opencv_live_device_path_sets_capture_mode(monkeypatch):
    import camera_drivers as drivers

    cv2 = _patch_videocapture(monkeypatch)
    original_exists = drivers.Path.exists

    def exists(self):
        if str(self) == "/dev/video0":
            return True
        return original_exists(self)

    monkeypatch.setattr(drivers.Path, "exists", exists)
    monkeypatch.setenv("CAMERA_SOURCE", "/dev/video0")
    _frame, meta = OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    cap = _FakeVideoCapture.instances[-1]
    assert cap.device == "/dev/video0"
    assert cap.sets[0][0] == cv2.CAP_PROP_FOURCC
    assert meta["width"] == 3840
    assert meta["fourcc"] == "MJPG"


def test_opencv_mjpeg_alias_maps_to_mjpg(monkeypatch):
    cv2 = _patch_videocapture(monkeypatch)
    monkeypatch.setenv("CAMERA_SOURCE", "0")
    monkeypatch.setenv("CAMERA_FOURCC", "mjpeg")
    OpenCvCameraDriver().capture(camera_id="usb", recipe_id="r")
    by_prop = dict(_FakeVideoCapture.instances[-1].sets)
    assert by_prop[cv2.CAP_PROP_FOURCC] == cv2.VideoWriter_fourcc(*"MJPG")
