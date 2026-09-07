"""End-customer billing orchestration and API."""

from fastapi.testclient import TestClient

from app.license_billing import LicenseBillingError, LicenseBillingService, validate_return_url
from app.licensing import LicenseManager, _features_from_server_list
from app.main import app, license_manager


def _mgr(tmp_path, monkeypatch, **env):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "license_state.json"))
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.schmitz.ms")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return LicenseManager()


def test_licadmin_feature_aliases_map_to_amx_gates():
    feats = _features_from_server_list(
        ["basic", "inspection", "Trends", "Export"],
        enabled=True,
        grant_core=True,
    )
    assert feats["inspection.run"] is True
    assert feats["inspection.read"] is True
    assert feats["dashboard_run"] is True
    assert feats["trends_filters"] is True
    assert feats["advanced_export"] is True


def test_validate_return_url_rejects_foreign_origin(monkeypatch):
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    monkeypatch.setenv("AMX_CORS_ORIGINS", "https://hmi.example")
    try:
        validate_return_url("https://evil.example/phish", request_origin="https://hmi.example")
        raise AssertionError("expected reject")
    except LicenseBillingError as exc:
        assert exc.status_code == 400


def test_list_plans_filters_product_id(tmp_path, monkeypatch):
    manager = _mgr(tmp_path, monkeypatch)

    def fake_plans(self):
        return [
            {"id": 1, "name": "Other", "productId": 1},
            {"id": 4, "name": "AMX Pro", "productId": 2, "features": ["inspection", "Trends"]},
        ]

    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.list_public_plans", fake_plans)
    plans = LicenseBillingService(manager).list_plans()
    assert [plan["id"] for plan in plans] == [4]


def test_complete_checkout_activates_server_license(tmp_path, monkeypatch):
    manager = _mgr(tmp_path, monkeypatch)

    def fake_result(self, session_id, email=None):
        return {
            "status": "completed",
            "readyToActivate": True,
            "sessionId": session_id,
            "licenseKey": "LIVE-KEY-4242",
            "customerEmail": email or "ops@example.com",
            "features": ["inspection", "Trends"],
        }

    def fake_activate(self, license_key=None):
        return {"success": True, "token": "tok", "message": "ok"}

    def fake_validate(self, online=True):
        return {
            "valid": True,
            "license": {
                "productId": 2,
                "type": "subscription",
                "expiresAt": "2026-12-01T00:00:00+00:00",
                "features": ["inspection", "Trends", "Export"],
            },
        }

    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.get_checkout_result", fake_result)
    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.activate", fake_activate)
    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.validate", fake_validate)

    result = LicenseBillingService(manager).complete_checkout(
        session_id="cs_test",
        customer_email="ops@example.com",
    )
    assert result["activated"] is True
    assert result["license"]["active"] is True
    assert result["license"]["mode"] == "server"
    assert "inspection.run" in result["license"]["features"]
    assert manager.stored_license_key() == "LIVE-KEY-4242"
    assert manager.stored_customer_email() == "ops@example.com"
    assert "licenseKey" not in result


def test_billing_status_without_key_is_available_false(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.schmitz.ms")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())

    client = TestClient(app)
    r = client.get("/api/v1/license/billing", headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["available"] is False


def test_billing_api_requires_server_and_hides_key(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.delenv("LICENSE_SERVER_URL", raising=False)
    monkeypatch.delenv("LICENSE_PRODUCT_ID", raising=False)
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())

    client = TestClient(app)
    r = client.get("/api/v1/license/plans", headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"})
    assert r.status_code == 503


def test_checkout_api_orchestrates(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.schmitz.ms")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    monkeypatch.delenv("ANOMALYMATRIX_ENV", raising=False)
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())

    def fake_checkout(self, **kwargs):
        assert kwargs["billing_plan_id"] == 8
        assert kwargs["customer_email"] == "ops@example.com"
        return {
            "sessionId": "cs_live",
            "url": "https://checkout.stripe.com/c/pay/cs_live",
            "billingModel": "subscription",
        }

    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.create_checkout_session", fake_checkout)
    client = TestClient(app)
    r = client.post(
        "/api/v1/license/checkout",
        json={
            "billing_plan_id": 8,
            "customer_email": "ops@example.com",
            "success_url": "http://127.0.0.1:5173/?checkout=success&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": "http://127.0.0.1:5173/?checkout=cancel",
        },
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1", "Origin": "http://127.0.0.1:5173"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["url"].startswith("https://checkout.stripe.com")


def test_billing_status_omits_raw_key(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.schmitz.ms")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(
        {
            **license_manager._default(),
            "licenseKey": "SUPER-SECRET-KEY",
            "licenseKeyMasked": "***-KEY",
            "customerEmail": "ops@example.com",
        }
    )

    def fake_billing(self, **kwargs):
        assert kwargs["license_key"] == "SUPER-SECRET-KEY"
        return {
            "licenseKey": "SUPER-SECRET-KEY",
            "productId": 2,
            "status": "active",
            "expiresAt": None,
            "features": ["inspection"],
            "hasStripeSubscription": True,
            "subscriptionStatus": "active",
            "cancelAtPeriodEnd": False,
            "canCancel": True,
            "canOpenPortal": True,
        }

    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.get_license_billing", fake_billing)
    client = TestClient(app)
    r = client.get(
        "/api/v1/license/billing",
        headers={"X-AMX-Role": "operator", "X-AMX-User": "operator-1"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "licenseKey" not in data
    assert data["license_key_masked"] == "***-KEY" or data["license_key_masked"].endswith("KEY")
    assert data["canCancel"] is True
