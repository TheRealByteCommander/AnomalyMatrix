"""Regression tests for post-merge production correctness fixes."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_gateway_requirements_include_httpx():
    req = (Path(__file__).resolve().parents[2] / "opcua-gateway" / "requirements.txt").read_text(encoding="utf-8")
    assert "httpx" in req


def test_edge_capture_fails_closed_in_production(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("EDGE_ACQUISITION_URL", "http://127.0.0.1:1")
    from app.services_edge import capture_frame

    with pytest.raises(RuntimeError, match="Edge capture failed"):
        capture_frame(camera_id="cam-01", recipe_id="recipe-default")


def test_edge_capture_requires_url_in_production(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.delenv("EDGE_ACQUISITION_URL", raising=False)
    from app.services_edge import capture_frame

    with pytest.raises(RuntimeError, match="EDGE_ACQUISITION_URL"):
        capture_frame()


def test_edge_capture_falls_back_outside_production(monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    monkeypatch.setenv("EDGE_ACQUISITION_URL", "http://127.0.0.1:1")
    from app.services_edge import capture_frame

    frame = capture_frame(camera_id="cam-01", recipe_id="recipe-default")
    assert frame.image_uri.startswith("synthetic://")


def test_minio_public_base_preferred(monkeypatch):
    monkeypatch.setenv("MINIO_PUBLIC_BASE", "/artifacts")
    from app.storage_minio import _public_object_url

    url = _public_object_url(
        endpoint="minio:9000",
        secure=False,
        bucket="heatmaps",
        object_name="i1/overlay.png",
    )
    assert url == "/artifacts/heatmaps/i1/overlay.png"
