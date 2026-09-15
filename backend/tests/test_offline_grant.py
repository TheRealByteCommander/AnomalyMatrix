"""Offline licenseGrant/v1 verification (node-locked, RS256)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.licensing import LicenseManager, _features_from_server_list
from app.licensing_sdk.offline import (
    AMX_OFFLINE_PUBLIC_KEY,
    DEMO_DEVICE_FINGERPRINT_RAW,
    DEMO_DEVICE_ID,
    OfflineLicenseError,
    verify_license_grant,
    verify_offline_license_file,
)
from app.main import app, license_manager

DEVICE_A = "a" * 64
DEVICE_B = "b" * 64


def _rsa_pems():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem.decode()


def _sign(private_pem, payload, *, expires_in=None, expires_at=None):
    claims = dict(payload)
    claims.setdefault("iat", int(datetime.now(timezone.utc).timestamp()))
    kwargs = {"algorithm": "RS256"}
    if expires_in is not None:
        claims["exp"] = int(datetime.now(timezone.utc).timestamp()) + int(expires_in)
    if expires_at is not None:
        claims["expiresAt"] = expires_at
    return jwt.encode(claims, private_pem, **kwargs)


def _payload(**overrides):
    data = {
        "grant": "licenseGrant",
        "licenseKey": "AMXB-OFFL-DEMO-0001",
        "productId": 2,
        "deviceId": DEVICE_A,
        "features": ["basic", "trends_filters"],
        "offline": True,
        "offlineGraceDays": None,
        "expiresAt": None,
    }
    data.update(overrides)
    return data


def _grant_file(token, public_pem, **overrides):
    body = {
        "format": "licenseGrant/v1",
        "algorithm": "RS256",
        "token": token,
        "publicKey": public_pem,
        "licenseKey": "AMXB-OFFL-DEMO-0001",
        "productId": 2,
        "deviceId": DEVICE_A,
        "features": ["basic", "trends_filters"],
        "expiresAt": None,
        "offlineGraceDays": None,
    }
    body.update(overrides)
    return body


def test_demo_device_id_matches_documented_hash():
    assert hashlib.sha256(DEMO_DEVICE_FINGERPRINT_RAW.encode("utf-8")).hexdigest() == DEMO_DEVICE_ID
    assert len(DEMO_DEVICE_ID) == 64


def test_verify_success_applies_signed_features():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    result = verify_license_grant(token, public_pem, DEVICE_A, expected_product_id=2)
    assert result["valid"] is True
    assert result["offline"] is True
    assert result["features"] == ["basic", "trends_filters"]
    assert result["licenseKey"] == "AMXB-OFFL-DEMO-0001"
    assert result["deviceId"] == DEVICE_A
    assert result["productId"] == 2


def test_wrong_device_id_rejects():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    with pytest.raises(OfflineLicenseError, match="different device"):
        verify_license_grant(token, public_pem, DEVICE_B, expected_product_id=2)


def test_wrong_product_id_rejects():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload(productId=99))
    with pytest.raises(OfflineLicenseError, match="different product"):
        verify_license_grant(token, public_pem, DEVICE_A, expected_product_id=2)


def test_bad_signature_rejects():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    tampered = token[:-6] + "abcdef"
    with pytest.raises(OfflineLicenseError, match="tampered"):
        verify_license_grant(tampered, public_pem, DEVICE_A, expected_product_id=2)


def test_file_public_key_cannot_replace_embedded_key():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    file_data = _grant_file(token, public_pem)
    with pytest.raises(OfflineLicenseError, match="tampered"):
        verify_offline_license_file(file_data, DEVICE_A, public_key=AMX_OFFLINE_PUBLIC_KEY, expected_product_id=2)


def test_expired_exp_claim_rejects():
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload(), expires_in=-60)
    with pytest.raises(OfflineLicenseError, match="expired"):
        verify_license_grant(token, public_pem, DEVICE_A, expected_product_id=2)


def test_expired_expires_at_claim_rejects():
    private_pem, public_pem = _rsa_pems()
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    token = _sign(private_pem, _payload(expiresAt=past))
    with pytest.raises(OfflineLicenseError, match="expired"):
        verify_license_grant(token, public_pem, DEVICE_A, expected_product_id=2)


def test_basic_and_trends_map_to_inspection_features():
    feats = _features_from_server_list(["basic", "trends_filters"], enabled=True, grant_core=True)
    assert feats["inspection.run"] is True
    assert feats["inspection.read"] is True
    assert feats["dashboard_run"] is True
    assert feats["trends_filters"] is True


def _mgr(tmp_path, monkeypatch, public_pem, device_id=DEVICE_A):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "license_state.json"))
    monkeypatch.setenv("LICENSE_GRANT_FILE", str(tmp_path / "license_grant.lic.json"))
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    monkeypatch.setenv("LICENSE_DEVICE_ID", device_id)
    monkeypatch.setenv("LICENSE_OFFLINE_ONLY", "true")
    monkeypatch.delenv("LICENSE_SERVER_URL", raising=False)
    monkeypatch.setattr("app.licensing_sdk.offline.AMX_OFFLINE_PUBLIC_KEY", public_pem)
    monkeypatch.setattr("app.licensing.AMX_OFFLINE_PUBLIC_KEY", public_pem)
    return LicenseManager()


def test_manager_import_grant_enables_inspection(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    manager = _mgr(tmp_path, monkeypatch, public_pem)
    status = manager.import_grant(_grant_file(token, public_pem))
    assert status["active"] is True
    assert status["offline"] is True
    assert status["mode"] == "offline"
    assert status["license_key"] == "AMXB-OFFL-DEMO-0001"
    assert status["device_id"] == DEVICE_A
    assert "inspection.run" in status["features"]
    assert "trends_filters" in status["features"]
    manager.enforce_feature("inspection.run")
    revalidated = manager.validate_once()
    assert revalidated["active"] is True
    assert revalidated["offline"] is True


def test_manager_rejects_wrong_device(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload(deviceId=DEVICE_B),)
    manager = _mgr(tmp_path, monkeypatch, public_pem, device_id=DEVICE_A)
    with pytest.raises(PermissionError, match="different device"):
        manager.import_grant(_grant_file(token, public_pem, deviceId=DEVICE_B))


def test_activate_key_requires_imported_grant(tmp_path, monkeypatch):
    _private_pem, public_pem = _rsa_pems()
    manager = _mgr(tmp_path, monkeypatch, public_pem)
    with pytest.raises(PermissionError, match="lic.json"):
        manager.activate("AMXB-OFFL-DEMO-0001")


def test_activate_key_matches_imported_grant(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    manager = _mgr(tmp_path, monkeypatch, public_pem)
    manager.import_grant(_grant_file(token, public_pem))
    status = manager.activate("AMXB-OFFL-DEMO-0001")
    assert status["active"] is True
    assert status["license_key"] == "AMXB-OFFL-DEMO-0001"
    with pytest.raises(PermissionError, match="does not match"):
        manager.activate("OTHER-KEY-9999")


def test_upgrade_replaces_grant(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    manager = _mgr(tmp_path, monkeypatch, public_pem)
    starter = _sign(private_pem, _payload(features=["basic"]))
    upgraded = _sign(
        private_pem,
        _payload(licenseKey="AMXB-OFFL-PRO-0002", features=["basic", "trends_filters", "advanced_export"]),
    )
    first = manager.import_grant(_grant_file(starter, public_pem, features=["basic"]))
    assert "trends_filters" not in first["features"] or first["tier"] in {"basic", "pro"}
    second = manager.import_grant(
        _grant_file(
            upgraded,
            public_pem,
            licenseKey="AMXB-OFFL-PRO-0002",
            features=["basic", "trends_filters", "advanced_export"],
        )
    )
    assert second["license_key"] == "AMXB-OFFL-PRO-0002"
    assert "advanced_export" in second["features"]
    assert "inspection.run" in second["features"]


def test_does_not_call_licadmin_when_grant_present(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.example.invalid")
    manager = _mgr(tmp_path, monkeypatch, public_pem)

    def boom(*_args, **_kwargs):
        raise AssertionError("licadmin must not be called for offline grants")

    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.activate", boom)
    monkeypatch.setattr("app.licensing_sdk.client.LicenseClient.validate", boom)
    manager.import_grant(_grant_file(token, public_pem))
    status = manager.validate_once()
    assert status["active"] is True
    assert status["offline"] is True


def test_import_api_and_status(tmp_path, monkeypatch):
    private_pem, public_pem = _rsa_pems()
    token = _sign(private_pem, _payload())
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_GRANT_FILE", str(tmp_path / "grant.lic.json"))
    monkeypatch.setenv("LICENSE_ENFORCE", "true")
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    monkeypatch.setenv("LICENSE_DEVICE_ID", DEVICE_A)
    monkeypatch.setenv("LICENSE_OFFLINE_ONLY", "true")
    monkeypatch.delenv("LICENSE_SERVER_URL", raising=False)
    monkeypatch.setattr("app.licensing_sdk.offline.AMX_OFFLINE_PUBLIC_KEY", public_pem)
    monkeypatch.setattr("app.licensing.AMX_OFFLINE_PUBLIC_KEY", public_pem)
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())

    client = TestClient(app)
    r = client.get("/api/v1/license/status", headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"})
    assert r.status_code == 200, r.text
    status = r.json()["data"]
    assert status["device_id"] == DEVICE_A
    assert status["offline"] is True
    assert status["billing_enabled"] is False

    imported = client.post(
        "/api/v1/license/import",
        json=_grant_file(token, public_pem),
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert imported.status_code == 200, imported.text
    body = imported.json()["data"]
    assert body["active"] is True
    assert body["offline"] is True
    assert body["license_key"] == "AMXB-OFFL-DEMO-0001"
    assert "inspection.run" in body["features"]

    keyed = client.post(
        "/api/v1/license/import",
        json={"license_key": "AMXB-OFFL-DEMO-0001"},
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert keyed.status_code == 200, keyed.text
    assert keyed.json()["data"]["active"] is True


def test_billing_disabled_for_product_two(tmp_path, monkeypatch):
    monkeypatch.setenv("LICENSE_STATE_FILE", str(tmp_path / "lic.json"))
    monkeypatch.setenv("LICENSE_PRODUCT_ID", "2")
    monkeypatch.setenv("LICENSE_SERVER_URL", "https://licadmin.schmitz.ms")
    monkeypatch.delenv("LICENSE_OFFLINE_ONLY", raising=False)
    license_manager.storage_path = tmp_path / "lic.json"
    license_manager._save(license_manager._default())
    client = TestClient(app)
    r = client.get("/api/v1/license/plans", headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"})
    assert r.status_code == 410
    checkout = client.post(
        "/api/v1/license/checkout",
        json={
            "billing_plan_id": 1,
            "customer_email": "ops@example.com",
            "success_url": "http://127.0.0.1:5173/?checkout=success",
            "cancel_url": "http://127.0.0.1:5173/?checkout=cancel",
        },
        headers={"X-AMX-Role": "admin", "X-AMX-User": "admin-1"},
    )
    assert checkout.status_code == 410
