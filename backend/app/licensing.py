from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass
class LicenseSnapshot:
    state: str
    message: str
    expiresAt: str | None
    graceUntil: str | None
    seats: dict
    device: dict
    features: dict

    @property
    def active(self) -> bool:
        return self.state in {"active", "offline", "grace"}

    @property
    def tier(self) -> str:
        if self.features.get("advanced_export"):
            return "enterprise"
        if self.features.get("trends_filters"):
            return "pro"
        return "basic" if self.active else "none"

    @property
    def token_present(self) -> bool:
        return bool(self.device.get("id") and self.device.get("id") != "unknown")

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


class LicenseManager:
    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or (Path(__file__).resolve().parents[1] / "data" / "license_state.json")
        self.validation_interval_sec = 300

    def _default(self) -> dict:
        return {
            "state": "invalid",
            "message": "License not activated",
            "expiresAt": None,
            "graceUntil": None,
            "seats": {"used": 0, "total": 0},
            "device": {"id": "unknown", "lastValidationUtc": datetime.now(timezone.utc).isoformat()},
            "features": {
                "dashboard_run": True,
                "inspection_detail": True,
                "inspection.run": True,
                "inspection.read": True,
                "trends_filters": False,
                "advanced_export": False,
            },
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

    def _to_snapshot(self, data: dict) -> LicenseSnapshot:
        return LicenseSnapshot(
            state=data.get("state", "invalid"),
            message=data.get("message", ""),
            expiresAt=data.get("expiresAt"),
            graceUntil=data.get("graceUntil"),
            seats=data.get("seats", {"used": 0, "total": 0}),
            device=data.get("device", {"id": "unknown"}),
            features=data.get("features", {}),
        )

    def validate_once(self) -> LicenseSnapshot:
        data = self._load()
        now = datetime.now(timezone.utc)

        if data.get("state") == "active" and data.get("expiresAt"):
            exp = datetime.fromisoformat(data["expiresAt"])
            if exp < now:
                data["state"] = "expired"
                data["message"] = "License expired"
                if not data.get("graceUntil"):
                    data["graceUntil"] = (now + timedelta(days=3)).isoformat()
                self._save(data)

        return self._to_snapshot(data)

    def snapshot(self) -> LicenseSnapshot:
        return self.validate_once()

    def activate(self, key: str, *, seats_requested: int = 1, device_id: str = "local-device") -> dict:
        now = datetime.now(timezone.utc)
        key = key.strip()

        if key.startswith("AMX-EXPIRED"):
            state = "expired"
            expires = now - timedelta(days=1)
            grace = now + timedelta(days=3)
            features = {
                "dashboard_run": True,
                "inspection_detail": True,
                "inspection.run": True,
                "inspection.read": True,
                "trends_filters": False,
                "advanced_export": False,
            }
            message = "License expired, grace active"
        elif key.startswith("AMX-OFFLINE"):
            state = "offline"
            expires = now + timedelta(days=14)
            grace = now + timedelta(days=2)
            features = {
                "dashboard_run": True,
                "inspection_detail": True,
                "inspection.run": True,
                "inspection.read": True,
                "trends_filters": True,
                "advanced_export": False,
            }
            message = "Offline validation mode"
        elif len(key) >= 8:
            state = "active"
            expires = now + timedelta(days=365)
            grace = None
            features = {
                "dashboard_run": True,
                "inspection_detail": True,
                "inspection.run": True,
                "inspection.read": True,
                "trends_filters": True,
                "advanced_export": True,
            }
            message = "License active"
        else:
            state = "invalid"
            expires = None
            grace = None
            features = {
                "dashboard_run": True,
                "inspection_detail": True,
                "inspection.run": True,
                "inspection.read": True,
                "trends_filters": False,
                "advanced_export": False,
            }
            message = "Invalid key"

        data = {
            "state": state,
            "message": message,
            "expiresAt": expires.isoformat() if expires else None,
            "graceUntil": grace.isoformat() if grace else None,
            "seats": {"used": 1 if state in {"active", "offline", "expired"} else 0, "total": max(1, int(seats_requested))},
            "device": {"id": device_id, "lastValidationUtc": now.isoformat()},
            "features": features,
            "licenseKeyMasked": f"***{key[-4:]}" if key else "",
        }
        self._save(data)
        snap = self.validate_once()
        return {"active": snap.active, "tier": snap.tier, "features": list(snap.features.keys())}

    def deactivate(self) -> dict:
        self._save(self._default())
        snap = self.validate_once()
        return {"active": snap.active, "tier": snap.tier, "features": list(snap.features.keys())}

    def enforce_feature(self, feature_name: str) -> None:
        # Default for MVP/dev: do not hard-block app unless explicitly enforced.
        if os.getenv("LICENSE_ENFORCE", "false").strip().lower() not in {"1", "true", "yes", "on"}:
            return

        snap = self.validate_once()
        if snap.state in {"invalid", "expired"}:
            raise PermissionError(f"Feature {feature_name} unavailable: license {snap.state}")

        if not snap.features.get(feature_name, False):
            raise PermissionError(f"Feature {feature_name} not enabled by license")
