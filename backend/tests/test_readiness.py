"""Readiness / version wiring tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.health import app_version, readiness_payload
from app.main import app

client = TestClient(app)


def test_health_returns_version_from_file(monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_VERSION", raising=False)
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["data"]["version"]
    assert r.json()["data"]["status"] == "ok"


def test_ready_ok_without_required_deps_in_dev(monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("EDGE_ACQUISITION_URL", raising=False)
    payload, ready = readiness_payload()
    assert ready is True
    assert payload["status"] == "ready"


def test_ready_fails_when_edge_required_in_prod(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("EDGE_ACQUISITION_URL", "http://127.0.0.1:1")
    payload, ready = readiness_payload()
    assert ready is False
    assert payload["checks"]["edge"]["ok"] is False


def test_app_version_env_override(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_VERSION", "9.9.9-test")
    assert app_version() == "9.9.9-test"


def test_docs_available_outside_production(monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    r = client.get("/docs")
    assert r.status_code == 200
