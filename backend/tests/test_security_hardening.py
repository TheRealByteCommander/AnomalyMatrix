"""Security hardening regression tests for production-ready controls."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core_store import CoreStore
from app.main import app
from app.production import cookie_secure, validate_production_config
from app.rbac import resolve_auth
from app.service_auth import SERVICE_TOKEN_HEADER


client = TestClient(app)


def test_unknown_dev_role_is_rejected_not_escalated(tmp_path, monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    monkeypatch.setenv("RBAC_ENFORCE", "false")
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-amx-role", b"superuser"), (b"x-amx-user", b"attacker")],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "scheme": "http",
        "query_string": b"",
    }
    request = Request(scope)
    with pytest.raises(Exception) as exc:
        resolve_auth(request, store)
    assert getattr(exc.value, "status_code", None) == 403


def test_contracts_and_license_require_authenticated_context(tmp_path, monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    assert client.get("/api/v1/contracts/events").status_code == 401
    assert client.get("/api/v1/license/status").status_code == 401


def test_session_cookie_sets_secure_flag_in_production(tmp_path, monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    monkeypatch.setenv("DATABASE_URL", "")
    assert cookie_secure() is True

    store = CoreStore(tmp_path)
    # Ensure password exists for login
    store.set_user_password("admin-1", "changeme")
    app.state.core_store = store

    # Temporarily allow non-prod auth path for login endpoint itself
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "dev")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    login = client.post("/api/v1/auth/login", json={"user_id": "admin-1", "password": "changeme"})
    assert login.status_code == 200
    set_cookie = login.headers.get("set-cookie", "")
    assert "amx_session=" in set_cookie
    assert "Secure" in set_cookie or "secure" in set_cookie.lower()


def test_license_admin_token_always_required_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("LICENSE_ADMIN_TOKEN", "expected-admin-token")
    monkeypatch.setenv("RBAC_ENFORCE", "false")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    r = client.post(
        "/api/v1/license/activate",
        json={"license_key": "K"},
        headers={"X-AMX-Role": "admin", "X-License-Admin-Token": "wrong"},
    )
    assert r.status_code == 403


def test_production_requires_service_auth_token(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("LICENSE_ADMIN_TOKEN", "unique-admin-token")
    monkeypatch.setenv("AMX_CORS_ORIGINS", "https://hmi.example")
    monkeypatch.setenv("RBAC_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "patchcore")
    monkeypatch.setenv("OPCUA_SECURITY_ENABLED", "true")
    monkeypatch.delenv("SERVICE_AUTH_TOKEN", raising=False)
    errors = validate_production_config()
    assert any("SERVICE_AUTH_TOKEN" in e for e in errors)


def test_bearer_invalid_does_not_fall_through_to_dev_headers(tmp_path, monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    monkeypatch.setenv("RBAC_ENFORCE", "false")
    monkeypatch.setenv("DATABASE_URL", "")
    store = CoreStore(tmp_path)
    app.state.core_store = store

    r = client.get(
        "/api/v1/inspections/recent",
        headers={"Authorization": "Bearer not-a-valid-token", "X-AMX-Role": "admin"},
    )
    assert r.status_code == 401


def test_edge_service_auth_middleware_rejects_without_token(monkeypatch):
    monkeypatch.setenv("SERVICE_AUTH_TOKEN", "edge-secret-token-1234567890")
    monkeypatch.setenv("ANOMALYMATRIX_ENV", "dev")
    import sys
    from pathlib import Path

    edge_root = Path(__file__).resolve().parents[2] / "edge-acquisition"
    sys.path.insert(0, str(edge_root))
    from service import app as edge_app  # noqa: WPS433

    edge_client = TestClient(edge_app)
    denied = edge_client.post("/capture", json={"camera_id": "cam-01"})
    assert denied.status_code == 401

    allowed = edge_client.post(
        "/capture",
        json={"camera_id": "cam-01"},
        headers={SERVICE_TOKEN_HEADER: "edge-secret-token-1234567890"},
    )
    assert allowed.status_code == 200
