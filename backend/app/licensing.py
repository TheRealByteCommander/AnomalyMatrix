"""AnomalyMatrix license manager.

Product 2 (industrial HMI) is offline / node-locked by default: vendor issues
a signed `.lic.json` grant, the PC verifies RS256 locally, and never calls
licadmin activate/validate or Stripe checkout.

Local bootstrap keys (`AMX-*`) remain available for install/CI when no grant
is present and the environment is not production.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .licensing_sdk import LicenseClient, LicensingApiError
from .licensing_sdk.offline import (
    AMX_OFFLINE_PUBLIC_KEY,
    OfflineLicenseError,
    load_offline_license_file,
    verify_offline_license_file,
)
from .production import is_production


@dataclass
class LicenseSnapshot:
    state: str
    message: str
    expiresAt: str | None
    graceUntil: str | None
    seats: dict
    device: dict
    features: dict
    token: str | None = None

    @property
    def active(self) -> bool:
        if self.state in {"active", "offline", "grace"}:
            return True
        # Honor grace window even if persisted state is still "expired".
        return self.state == "expired" and self.grace_active

    def _feature_enabled(self, name: str) -> bool:
        if isinstance(self.features, dict):
            return bool(self.features.get(name, False))
        if isinstance(self.features, list):
            return name in self.features
        return False

    @property
    def tier(self) -> str:
        if self._feature_enabled("advanced_export"):
            return "enterprise"
        if self._feature_enabled("trends_filters"):
            return "pro"
        return "basic" if self.active else "none"

    @property
    def token_present(self) -> bool:
        return bool(self.token) or bool(self.device.get("id") and self.device.get("id") not in {"unknown", ""})

    @property
    def valid_until(self) -> str | None:
        return self.expiresAt

    @property
    def last_validation_at(self) -> str | None:
        return self.device.get("lastValidationUtc")

    @property
    def offline_grace_until(self) -> str | None:
        return self.graceUntil

    @property
    def grace_active(self) -> bool:
        if not self.graceUntil:
            return False
        try:
            return datetime.fromisoformat(self.graceUntil) > datetime.now(timezone.utc)
        except Exception:
            return False

    @property
    def last_error(self) -> str | None:
        return None if self.active else self.message

    @property
    def enabled_features(self) -> list[str]:
        if isinstance(self.features, dict):
            return [name for name, on in self.features.items() if on]
        if isinstance(self.features, list):
            return list(self.features)
        return []


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _offline_grace_hours() -> int:
    try:
        return max(1, int(os.getenv("LICENSE_OFFLINE_GRACE_HOURS", "72")))
    except ValueError:
        return 72


def _server_url() -> str:
    return os.getenv("LICENSE_SERVER_URL", "").strip().rstrip("/")


def _product_id() -> int | None:
    raw = os.getenv("LICENSE_PRODUCT_ID", "2").strip()
    if not raw:
        return 2
    try:
        return int(raw)
    except ValueError:
        return None


def _offline_only() -> bool:
    raw = os.getenv("LICENSE_OFFLINE_ONLY", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    return _product_id() == 2


def compute_device_id() -> str:
    """Stable SHA-256 hex fingerprint (same as LicenseClient.get_device_id)."""
    override = os.getenv("LICENSE_DEVICE_ID", "").strip() or None
    pid = _product_id() or 2
    return LicenseClient(
        server_url=_server_url() or "http://127.0.0.1",
        product_id=pid,
        device_id=override,
    ).get_device_id()


def _features_from_server_list(
    feature_names: list | None,
    *,
    enabled: bool,
    grant_core: bool = False,
) -> dict:
    """Map server feature strings onto AnomalyMatrix feature flags."""
    names = {str(x).strip() for x in (feature_names or []) if str(x).strip()}
    base = {
        "dashboard_run": enabled,
        "inspection_detail": enabled,
        "inspection.run": enabled,
        "inspection.read": enabled,
        "trends_filters": False,
        "advanced_export": False,
    }
    if not names:
        return base

    aliases = {
        "inspection.run": "inspection.run",
        "inspection_run": "inspection.run",
        "inspection": "inspection.run",
        "run_inspection": "inspection.run",
        "inspection.read": "inspection.read",
        "inspection_read": "inspection.read",
        "dashboard_run": "dashboard_run",
        "dashboard": "dashboard_run",
        "inspection_detail": "inspection_detail",
        "basic": "dashboard_run",
        "trends_filters": "trends_filters",
        "trends": "trends_filters",
        "pro": "trends_filters",
        "advanced_export": "advanced_export",
        "enterprise": "advanced_export",
        "export": "advanced_export",
    }
    aliases_lc = {key.lower(): value for key, value in aliases.items()}
    out = {k: False for k in base}
    matched = False
    for name in names:
        key = aliases_lc.get(name.lower(), name if name in out else None)
        if key:
            out[key] = True
            matched = True
    if matched:
        if grant_core:
            out["inspection.run"] = True
            out["inspection.read"] = True
            out["dashboard_run"] = True
            out["inspection_detail"] = True
        return out
    # Unknown feature names only — grant base product features for a valid license.
    return base if grant_core or enabled else out


class LicenseManager:
    def __init__(self, storage_path: Path | None = None):
        env_path = os.getenv("LICENSE_STATE_FILE", "").strip()
        default_path = Path(__file__).resolve().parents[1] / "data" / "license_state.json"
        self.storage_path = storage_path or (Path(env_path) if env_path else default_path)
        try:
            self.validation_interval_sec = max(30, int(os.getenv("LICENSE_VALIDATE_INTERVAL_SEC", "300")))
        except ValueError:
            self.validation_interval_sec = 300

    @property
    def enforce(self) -> bool:
        return _env_bool("LICENSE_ENFORCE", default=False)

    @property
    def server_configured(self) -> bool:
        if self.offline_only:
            return False
        return bool(_server_url() and _product_id() is not None)

    @property
    def offline_only(self) -> bool:
        return _offline_only()

    def grant_path(self) -> Path:
        env_path = os.getenv("LICENSE_GRANT_FILE", "").strip()
        if env_path:
            return Path(env_path)
        return self.storage_path.parent / "license_grant.lic.json"

    def current_device_id(self) -> str:
        return compute_device_id()

    def _chmod_private(self, path: Path) -> None:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def _base_features(self, *, enabled: bool) -> dict:
        return {
            "dashboard_run": enabled,
            "inspection_detail": enabled,
            "inspection.run": enabled,
            "inspection.read": enabled,
            "trends_filters": enabled,
            "advanced_export": False,
        }

    def _default(self) -> dict:
        enabled = not self.enforce
        return {
            "state": "invalid",
            "message": "License not activated",
            "expiresAt": None,
            "graceUntil": None,
            "seats": {"used": 0, "total": 0},
            "device": {"id": "unknown", "lastValidationUtc": datetime.now(timezone.utc).isoformat()},
            "features": self._base_features(enabled=enabled),
            "token": None,
            "licenseKey": None,
            "customerEmail": None,
            "mode": "offline" if self.offline_only else ("server" if self.server_configured else "local"),
            "offline": bool(self.offline_only),
        }

    def _load(self) -> dict:
        if not self.storage_path.exists():
            return self._default()
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception:
            return self._default()

    def _save(self, data: dict) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._chmod_private(self.storage_path)

    def _normalize(self, data: dict) -> dict:
        if "expiresAt" not in data and "valid_until" in data:
            data["expiresAt"] = data.get("valid_until")
        if "graceUntil" not in data and "offline_grace_until" in data:
            data["graceUntil"] = data.get("offline_grace_until")
        if "state" not in data:
            data["state"] = "active" if data.get("active") else "invalid"
        if "token" not in data and data.get("token") is None:
            data["token"] = data.get("token")  # keep explicit
        # Legacy list features → dict (exact flags only; no implicit core grant)
        feats = data.get("features")
        if isinstance(feats, list):
            data["features"] = _features_from_server_list(feats, enabled=True, grant_core=False)
        return data

    def _to_snapshot(self, data: dict) -> LicenseSnapshot:
        data = self._normalize(dict(data))
        return LicenseSnapshot(
            state=data.get("state", "invalid"),
            message=data.get("message", ""),
            expiresAt=data.get("expiresAt"),
            graceUntil=data.get("graceUntil"),
            seats=data.get("seats", {"used": 0, "total": 0}),
            device=data.get("device", {"id": "unknown"}),
            features=data.get("features", {}),
            token=data.get("token"),
        )

    def _client(self, *, license_key: str | None = None, token: str | None = None) -> LicenseClient:
        url = _server_url()
        pid = _product_id()
        if not url or pid is None:
            raise RuntimeError("LICENSE_SERVER_URL and LICENSE_PRODUCT_ID (integer) required")
        token_path = self.storage_path.parent / f"license_token_{pid}.json"
        client = LicenseClient(
            server_url=url,
            product_id=pid,
            license_key=license_key,
            token_file=token_path,
            device_id=os.getenv("LICENSE_DEVICE_ID", "").strip() or None,
        )
        if token:
            client.set_token(token)
        return client

    def _status_dict(self, data: dict) -> dict:
        snap = self._to_snapshot(data)
        return {
            "active": snap.active,
            "tier": snap.tier,
            "features": snap.enabled_features,
            "token_present": snap.token_present,
            "valid_until": snap.valid_until,
            "last_validation_at": snap.last_validation_at,
            "offline_grace_until": snap.offline_grace_until,
            "grace_active": snap.grace_active,
            "last_error": snap.last_error,
            "state": "grace" if (snap.state == "expired" and snap.grace_active) else snap.state,
            "message": snap.message,
            "mode": data.get("mode")
            or ("offline" if self.offline_only else ("server" if self.server_configured else "local")),
            "offline": bool(
                data.get("offline")
                or data.get("mode") == "offline"
                or snap.state == "offline"
                or self.offline_only
            ),
            "device_id": self.current_device_id(),
            "license_key": data.get("licenseKey"),
            "product_id": _product_id(),
            "billing_enabled": False if self.offline_only else self.server_configured,
        }

    def validate_once(self) -> dict:
        data = self._normalize(self._load())
        now = datetime.now(timezone.utc)

        if self.grant_path().exists() or (
            (data.get("mode") == "offline" or data.get("offline"))
            and data.get("token")
            and not str(data.get("token") or "").startswith("local-")
        ):
            return self._validate_offline_grant(data, now)

        if self.offline_only:
            data.setdefault("device", {})["id"] = self.current_device_id()
            data["device"]["lastValidationUtc"] = now.isoformat()
            data["mode"] = data.get("mode") or "offline"
            data["offline"] = True
            self._save(data)
            return self._status_dict(data)

        if self.server_configured and data.get("token"):
            return self._validate_server(data, now)

        # Local / file-only path (CI, installer bootstrap without license server)
        if data.get("state") == "active" and data.get("expiresAt"):
            try:
                exp = datetime.fromisoformat(data["expiresAt"])
            except ValueError:
                exp = None
            if exp and exp < now:
                data["state"] = "expired"
                data["message"] = "License expired"
                if not data.get("graceUntil"):
                    data["graceUntil"] = (now + timedelta(hours=_offline_grace_hours())).isoformat()
                # Enter grace for runtime access
                if datetime.fromisoformat(data["graceUntil"]) > now:
                    data["state"] = "grace"
                    data["message"] = "License expired, grace active"
                self._save(data)

        if data.get("state") == "expired" and data.get("graceUntil"):
            try:
                if datetime.fromisoformat(data["graceUntil"]) > now:
                    data["state"] = "grace"
                    data["message"] = "License expired, grace active"
                    self._save(data)
            except ValueError:
                pass

        data.setdefault("device", {})["lastValidationUtc"] = now.isoformat()
        self._save(data)
        return self._status_dict(data)

    def _validate_server(self, data: dict, now: datetime) -> dict:
        client = self._client(license_key=data.get("licenseKey"), token=data.get("token"))
        try:
            result = client.validate(online=True)
        except LicensingApiError as exc:
            result = {"valid": False, "message": str(exc), "network_error": exc.code == "NETWORK_ERROR"}

        data.setdefault("device", {})
        data["device"]["id"] = client.get_device_id()
        data["device"]["lastValidationUtc"] = now.isoformat()

        if result.get("valid"):
            lic = result.get("license") or {}
            feature_list = lic.get("features") if isinstance(lic, dict) else None
            data["features"] = _features_from_server_list(
                feature_list if isinstance(feature_list, list) else None,
                enabled=True,
                grant_core=True,
            )
            expires = lic.get("expiresAt") if isinstance(lic, dict) else None
            data["expiresAt"] = expires
            if result.get("offline") or result.get("network_error"):
                data["state"] = "offline"
                data["message"] = "Offline validation (server unreachable)"
                if not data.get("graceUntil"):
                    data["graceUntil"] = (now + timedelta(hours=_offline_grace_hours())).isoformat()
            else:
                data["state"] = "active"
                data["message"] = "License active"
                data["graceUntil"] = None
            data["seats"] = data.get("seats") or {"used": 1, "total": 1}
            self._save(data)
            return self._status_dict(data)

        # Invalid online — try grace if we still have a recent window
        msg = result.get("message") or "License validation failed"
        if data.get("graceUntil"):
            try:
                if datetime.fromisoformat(data["graceUntil"]) > now:
                    data["state"] = "grace"
                    data["message"] = f"Grace active after validation failure: {msg}"
                    self._save(data)
                    return self._status_dict(data)
            except ValueError:
                pass

        # Start grace on first failure after a previously active/offline token
        if data.get("state") in {"active", "offline", "grace"} and result.get("network_error"):
            data["graceUntil"] = (now + timedelta(hours=_offline_grace_hours())).isoformat()
            data["state"] = "grace"
            data["message"] = f"Grace active (network): {msg}"
            self._save(data)
            return self._status_dict(data)

        data["state"] = "invalid"
        data["message"] = msg
        # Keep token for support diagnostics but mark inactive
        self._save(data)
        return self._status_dict(data)

    def snapshot(self) -> LicenseSnapshot:
        return self._to_snapshot(self._load())

    def public_status(self) -> dict:
        data = self._normalize(self._load())
        status = self._status_dict(data)
        status.update(self.billing_hints())
        return status

    def _persist_grant_file(self, file_data: dict) -> None:
        path = self.grant_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(file_data, indent=2), encoding="utf-8")
        self._chmod_private(path)

    def _clear_grant_file(self) -> None:
        path = self.grant_path()
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    def _verify_grant_source(self, source, *, now: datetime | None = None) -> dict:
        try:
            return verify_offline_license_file(
                source,
                device_id=self.current_device_id(),
                public_key=AMX_OFFLINE_PUBLIC_KEY,
                now=now,
                expected_product_id=_product_id(),
            )
        except OfflineLicenseError as exc:
            raise PermissionError(str(exc)) from exc

    def _apply_offline_claims(self, claims: dict, *, file_data: dict | None = None) -> dict:
        now = datetime.now(timezone.utc)
        feature_list = claims.get("features") if isinstance(claims.get("features"), list) else []
        features = _features_from_server_list(feature_list, enabled=True, grant_core=True)
        key = str(claims.get("licenseKey") or "").strip()
        expires = claims.get("expiresAt")
        if expires is not None and not isinstance(expires, str):
            expires = None
        data = {
            "state": "offline",
            "message": "Offline license active (node-locked)",
            "expiresAt": expires,
            "graceUntil": None,
            "seats": {"used": 1, "total": 1},
            "device": {"id": self.current_device_id(), "lastValidationUtc": now.isoformat()},
            "features": features,
            "token": claims.get("token"),
            "licenseKey": key or None,
            "licenseKeyMasked": f"***{key[-4:]}" if len(key) >= 4 else None,
            "customerEmail": self._load().get("customerEmail"),
            "mode": "offline",
            "offline": True,
            "productId": claims.get("productId"),
        }
        if file_data is not None:
            self._persist_grant_file(file_data)
        self._save(data)
        return self._status_dict(data)

    def _validate_offline_grant(self, data: dict, now: datetime) -> dict:
        path = self.grant_path()
        if not path.exists():
            data["state"] = "invalid"
            data["message"] = "Offline license file missing"
            data["offline"] = True
            data["mode"] = "offline"
            data.setdefault("device", {})["id"] = self.current_device_id()
            data["device"]["lastValidationUtc"] = now.isoformat()
            self._save(data)
            return self._status_dict(data)
        try:
            claims = self._verify_grant_source(path, now=now)
        except PermissionError as exc:
            msg = str(exc)
            expired = "expired" in msg.lower()
            if expired and data.get("graceUntil"):
                try:
                    if datetime.fromisoformat(data["graceUntil"]) > now:
                        data["state"] = "grace"
                        data["message"] = f"Grace active after offline grant expiry: {msg}"
                        data["offline"] = True
                        data["mode"] = "offline"
                        self._save(data)
                        return self._status_dict(data)
                except ValueError:
                    pass
            data["state"] = "expired" if expired else "invalid"
            data["message"] = msg
            data["offline"] = True
            data["mode"] = "offline"
            data.setdefault("device", {})["id"] = self.current_device_id()
            data["device"]["lastValidationUtc"] = now.isoformat()
            if expired and not data.get("graceUntil"):
                grace_days = None
                try:
                    raw_file = load_offline_license_file(path)
                    grace_days = raw_file.get("offlineGraceDays")
                except (OSError, json.JSONDecodeError, OfflineLicenseError, TypeError):
                    grace_days = None
                hours = _offline_grace_hours()
                if isinstance(grace_days, int) and grace_days > 0:
                    hours = max(1, grace_days * 24)
                data["graceUntil"] = (now + timedelta(hours=hours)).isoformat()
                data["state"] = "grace"
                data["message"] = f"License expired, grace active: {msg}"
            self._save(data)
            return self._status_dict(data)
        return self._apply_offline_claims(claims)

    def import_grant(self, source, *, license_key: str | None = None) -> dict:
        try:
            file_data = load_offline_license_file(source)
            claims = self._verify_grant_source(file_data)
        except OfflineLicenseError as exc:
            raise PermissionError(str(exc)) from exc
        grant_key = str(claims.get("licenseKey") or "").strip()
        entered = (license_key or "").strip()
        if entered and grant_key and entered != grant_key:
            raise PermissionError("License number does not match the imported grant")
        return self._apply_offline_claims(claims, file_data=file_data)

    def _allow_local_bootstrap(self, key: str) -> bool:
        if not key.startswith("AMX-"):
            return False
        if _env_bool("LICENSE_ALLOW_LOCAL_KEYS", default=False):
            return True
        return not is_production()

    def activate(self, key: str, *, seats_requested: int = 1, device_id: str = "local-device") -> dict:
        key = key.strip()
        if not key:
            raise ValueError("license key required")

        if self.grant_path().exists():
            claims = self._verify_grant_source(self.grant_path())
            grant_key = str(claims.get("licenseKey") or "").strip()
            if grant_key and key != grant_key:
                raise PermissionError("License number does not match the imported grant")
            return self._apply_offline_claims(claims)

        if self.offline_only:
            if self._allow_local_bootstrap(key):
                return self._activate_local(key, seats_requested=seats_requested, device_id=device_id)
            raise PermissionError("Import a signed .lic.json grant before entering a license number")

        if self.server_configured and not _env_bool("LICENSE_ALLOW_LOCAL_KEYS", default=False):
            return self._activate_server(key)

        return self._activate_local(key, seats_requested=seats_requested, device_id=device_id)

    def _activate_server(self, key: str) -> dict:
        now = datetime.now(timezone.utc)
        client = self._client(license_key=key)
        try:
            result = client.activate(key)
        except LicensingApiError as exc:
            data = self._default()
            data["state"] = "invalid"
            data["message"] = f"Activation failed: [{exc.code}] {exc.message}"
            data["device"] = {"id": client.get_device_id(), "lastValidationUtc": now.isoformat()}
            self._save(data)
            raise PermissionError(data["message"]) from exc

        if not result.get("success"):
            data = self._default()
            data["state"] = "invalid"
            data["message"] = result.get("message", "Activation failed")
            self._save(data)
            raise PermissionError(data["message"])

        token = result["token"]
        # Validate immediately to pull features/expiry
        client.set_token(token)
        validation = client.validate(online=True)
        lic = validation.get("license") or {} if validation.get("valid") else {}
        features = _features_from_server_list(
            lic.get("features") if isinstance(lic, dict) else None,
            enabled=True,
            grant_core=True,
        )
        data = {
            "state": "active" if validation.get("valid") else "invalid",
            "message": result.get("message", "License active")
            if validation.get("valid")
            else validation.get("message", "Activated but validation failed"),
            "expiresAt": lic.get("expiresAt") if isinstance(lic, dict) else None,
            "graceUntil": None,
            "seats": {"used": 1, "total": 1},
            "device": {"id": client.get_device_id(), "lastValidationUtc": now.isoformat()},
            "features": features,
            "token": token,
            "licenseKey": key,
            "licenseKeyMasked": f"***{key[-4:]}",
            "customerEmail": self._load().get("customerEmail"),
            "mode": "server",
        }
        self._save(data)
        return self._status_dict(data)

    def _activate_local(self, key: str, *, seats_requested: int, device_id: str) -> dict:
        now = datetime.now(timezone.utc)

        if key.startswith("AMX-EXPIRED"):
            state = "grace"
            expires = now - timedelta(days=1)
            grace = now + timedelta(hours=_offline_grace_hours())
            features = self._base_features(enabled=True)
            features["trends_filters"] = False
            message = "License expired, grace active"
        elif key.startswith("AMX-OFFLINE"):
            state = "offline"
            expires = now + timedelta(days=14)
            grace = now + timedelta(days=2)
            features = self._base_features(enabled=True)
            features["trends_filters"] = True
            message = "Offline validation mode"
        elif len(key) >= 8:
            state = "active"
            expires = now + timedelta(days=365)
            grace = None
            features = self._base_features(enabled=True)
            features["trends_filters"] = True
            features["advanced_export"] = True
            message = "License active (local bootstrap)"
        else:
            state = "invalid"
            expires = None
            grace = None
            features = self._base_features(enabled=not self.enforce)
            message = "Invalid key"

        data = {
            "state": state,
            "message": message,
            "expiresAt": expires.isoformat() if expires else None,
            "graceUntil": grace.isoformat() if grace else None,
            "seats": {
                "used": 1 if state in {"active", "offline", "grace", "expired"} else 0,
                "total": max(1, int(seats_requested)),
            },
            "device": {"id": device_id, "lastValidationUtc": now.isoformat()},
            "features": features,
            "licenseKeyMasked": f"***{key[-4:]}" if key else "",
            "licenseKey": key,
            "token": f"local-{key[:8]}" if state != "invalid" else None,
            "mode": "local",
        }
        self._save(data)
        return self.validate_once()

    def deactivate(self) -> dict:
        data = self._load()
        self._clear_grant_file()
        if (not self.offline_only) and self.server_configured and data.get("licenseKey") and data.get("token"):
            try:
                client = self._client(license_key=data.get("licenseKey"), token=data.get("token"))
                client.deactivate()
            except (LicensingApiError, ValueError, RuntimeError):
                # Still clear local state even if server call fails.
                pass
        self._save(self._default())
        return self.public_status()

    def enforce_feature(self, feature_name: str) -> None:
        state = self._normalize(self._load())
        snap = self._to_snapshot(state)

        if self.enforce and not snap.active:
            raise PermissionError("License not active")

        features = state.get("features", {})
        enabled = False
        if isinstance(features, dict):
            enabled = bool(features.get(feature_name, False))
        elif isinstance(features, list):
            enabled = feature_name in features

        # During grace/offline, keep previously granted features.
        if not enabled and snap.active and snap.state in {"grace", "offline"}:
            enabled = feature_name in {"inspection.run", "inspection.read", "dashboard_run", "inspection_detail"}

        if not enabled:
            raise PermissionError(f"Feature {feature_name} not enabled by license")

    def remember_customer_email(self, email: str | None) -> None:
        cleaned = (email or "").strip().lower()
        if not cleaned or "@" not in cleaned:
            return
        data = self._normalize(self._load())
        data["customerEmail"] = cleaned
        self._save(data)

    def stored_customer_email(self) -> str | None:
        email = self._load().get("customerEmail")
        if isinstance(email, str) and "@" in email:
            return email.strip().lower()
        return None

    def stored_license_key(self) -> str | None:
        key = self._load().get("licenseKey")
        if isinstance(key, str) and key.strip():
            return key.strip()
        return None

    def billing_hints(self) -> dict:
        data = self._load()
        email = data.get("customerEmail") if isinstance(data.get("customerEmail"), str) else ""
        return {
            "billing_enabled": False if self.offline_only else self.server_configured,
            "customer_email_masked": _mask_email(email),
            "license_key_masked": data.get("licenseKeyMasked") or _mask_key(data.get("licenseKey")),
        }


def _mask_email(email: str | None) -> str | None:
    raw = (email or "").strip()
    if "@" not in raw:
        return None
    local, _, domain = raw.partition("@")
    if not local or not domain:
        return None
    visible = local[:1]
    return f"{visible}***@{domain.lower()}"


def _mask_key(key: str | None) -> str | None:
    raw = (key or "").strip()
    if len(raw) < 4:
        return None
    return f"***{raw[-4:]}"
