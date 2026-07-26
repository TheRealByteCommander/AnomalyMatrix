"""Server-mode licensing against software-licensing-concept API (mocked)."""

from datetime import datetime, timedelta, timezone

import jwt

from app.licensing import LicenseManager, _features_from_server_list
from app.licensing_sdk import LicenseClient, LicensingApiError


def _mgr(tmp_path, monkeypatch, **env):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "license_state.json"))
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://license.test")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "42")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return LicenseManager()


def test_features_from_server_list_maps_aliases():
    feats = _features_from_server_list(["pro", "enterprise"], enabled=True, grant_core=True)
    assert feats["inspection.run"] is True
    assert feats["trends_filters"] is True
    assert feats["advanced_export"] is True


def test_server_activate_persists_token(tmp_path, monkeypatch):
    m = _mgr(tmp_path, monkeypatch)
    token = jwt.encode(
        {
            "productId": 42,
            "features": ["inspection.run", "trends"],
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        key="secret",
        algorithm="HS256",
    )

    def fake_activate(self, license_key=None):
        self.set_token(token)
        self._save_token(token)
        self.license_key = license_key
        return {"success": True, "token": token, "message": "ok"}

    def fake_validate(self, online=True):
        return {
            "valid": True,
            "license": {
                "productId": 42,
                "type": "subscription",
                "expiresAt": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "features": ["inspection.run", "trends_filters"],
            },
        }

    monkeypatch.setattr(LicenseClient, "activate", fake_activate)
    monkeypatch.setattr(LicenseClient, "validate", fake_validate)

    st = m.activate("REAL-KEY-1234")
    assert st["active"] is True
    assert st["mode"] == "server"
    assert "inspection.run" in st["features"]
    assert m.snapshot().token == token


def test_server_validate_enters_grace_on_network_error(tmp_path, monkeypatch):
    m = _mgr(tmp_path, monkeypatch)
    now = datetime.now(timezone.utc)
    m._save(
        {
            "state": "active",
            "message": "ok",
            "expiresAt": (now + timedelta(days=10)).isoformat(),
            "graceUntil": None,
            "token": "tok",
            "licenseKey": "KEY",
            "features": {
                "inspection.run": True,
                "inspection.read": True,
                "dashboard_run": True,
                "inspection_detail": True,
                "trends_filters": False,
                "advanced_export": False,
            },
            "device": {"id": "dev", "lastValidationUtc": now.isoformat()},
            "seats": {"used": 1, "total": 1},
        }
    )

    def boom(self, online=True):
        raise LicensingApiError("NETWORK_ERROR", "connection refused")

    monkeypatch.setattr(LicenseClient, "validate", boom)
    st = m.validate_once()
    assert st["active"] is True
    assert st["grace_active"] is True or st["state"] in {"grace", "offline"}


def test_activate_works_when_enforce_and_inactive(tmp_path, monkeypatch):
    """Regression: license.admin must not require inspection.run feature."""
    from fastapi.testclient import TestClient

    from app.main import app, license_manager

    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_ADMIN_TOKEN", "adm")
    monkeypatch.delenv("LICENSE_SERVER_URL", raising=False)
    monkeypatch.delenv("LICENSE_PRODUCT_ID", raising=False)
    # Reset manager storage for this test process
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())

    client = TestClient(app)
    r = client.post(
        "/api/v1/license/activate",
        json={"license_key": "AMX-INSTALL-testdevice01"},
        headers={"X-License-Admin-Token": "adm", "X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True or body.get("data", {}).get("active") is True


def test_product_id_must_be_integer(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "license_state.json"))
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://license.test")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "anomalymatrix")
    m = LicenseManager()
    assert m.server_configured is False
