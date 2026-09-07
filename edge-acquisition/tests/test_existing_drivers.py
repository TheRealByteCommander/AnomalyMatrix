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
