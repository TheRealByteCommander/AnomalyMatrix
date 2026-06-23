import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.production import validate_production_config

client = TestClient(app)


def test_production_config_rejects_defaults(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET", "short")
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("LICENSE_ADMIN_TOKEN", "anomaly-token")
    monkeypatch.setenv("RBAC_ENFORCE", "false")
    errors = validate_production_config()
    assert any("JWT_SECRET" in e for e in errors)
    assert any("RBAC_ENFORCE" in e for e in errors)


def test_production_requires_auth_header(monkeypatch, tmp_path):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    from app.core_store import CoreStore

    store = CoreStore(tmp_path)
    app.state.core_store = store
    r = client.get("/api/v1/inspections/recent")
    assert r.status_code == 401


def test_rbac_enforced_blocks_operator_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    monkeypatch.setenv("DATABASE_URL", "")
    from app.core_store import CoreStore

    store = CoreStore(tmp_path)
    app.state.core_store = store
    r = client.post(
        "/api/v1/feedback",
        json={"inspection_id": "x", "verdict": "needs_review"},
        headers={"X-AMX-Role": "operator"},
    )
    assert r.status_code == 403
