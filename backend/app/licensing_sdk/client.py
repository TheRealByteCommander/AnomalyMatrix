"""License Client SDK — httpx variant for AnomalyMatrix backend."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import jwt

from .trpc import raise_for_trpc_error, unwrap_result, wrap_input


class LicensingApiError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class LicenseClient:
    """Client for license activation and validation against the BC license server."""

    def __init__(
        self,
        server_url: str,
        product_id: int,
        license_key: Optional[str] = None,
        *,
        token_file: Path | None = None,
        timeout_sec: float = 10.0,
        device_id: str | None = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.product_id = int(product_id)
        self.license_key = license_key
        self._token: Optional[str] = None
        self._timeout = timeout_sec
        self._device_id_override = device_id
        self._token_file = token_file or self._default_token_path()

    def _default_token_path(self) -> Path:
        if platform.system() == "Windows":
            base_dir = Path(os.getenv("APPDATA", ".")) / "LicenseSDK"
        else:
            base_dir = Path.home() / ".license_sdk"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"license_{self.product_id}.token"

    def get_device_id(self) -> str:
        if self._device_id_override:
            return self._device_id_override
        system_info = f"{platform.node()}-{platform.machine()}-{platform.system()}"
        try:
            machine_id = Path("/etc/machine-id")
            if machine_id.exists():
                system_info += f"-{machine_id.read_text(encoding='utf-8').strip()}"
            else:
                import uuid

                system_info += f"-{uuid.getnode()}"
        except OSError:
            pass
        return hashlib.sha256(system_info.encode()).hexdigest()

    def _save_token(self, token: str) -> None:
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        self._token_file.write_text(
            json.dumps({"token": token, "saved_at": datetime.now(timezone.utc).isoformat()}),
            encoding="utf-8",
        )

    def _load_token(self) -> Optional[str]:
        try:
            if self._token_file.exists():
                data = json.loads(self._token_file.read_text(encoding="utf-8"))
                return data.get("token")
        except (OSError, json.JSONDecodeError):
            return None
        return None

    def set_token(self, token: str | None) -> None:
        self._token = token

    @property
    def token(self) -> Optional[str]:
        if not self._token:
            self._token = self._load_token()
        return self._token

    def _parse_response(self, response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError as exc:
            raise LicensingApiError("BAD_RESPONSE", f"Non-JSON response ({response.status_code})") from exc

        try:
            raise_for_trpc_error(body, response.is_success)
        except LicensingApiError:
            raise
        except Exception as exc:
            # Upstream helper raises generic Exception("[CODE] message")
            text = str(exc)
            if text.startswith("[") and "]" in text:
                code, _, msg = text[1:].partition("]")
                raise LicensingApiError(code.strip(), msg.strip()) from exc
            raise LicensingApiError("UNKNOWN", text) from exc

        return unwrap_result(body)

    def _post(self, procedure: str, payload: dict[str, Any]) -> Any:
        url = f"{self.server_url}/api/trpc/{procedure}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=wrap_input(payload))
        except httpx.HTTPError as exc:
            raise LicensingApiError("NETWORK_ERROR", str(exc)) from exc
        return self._parse_response(response)

    def _get(self, procedure: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.server_url}/api/trpc/{procedure}"
        params = {"input": json.dumps(wrap_input(payload or {}))}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise LicensingApiError("NETWORK_ERROR", str(exc)) from exc
        return self._parse_response(response)

    def list_public_plans(self) -> list[dict[str, Any]]:
        data = self._get("stripe.plans.listPublic", {})
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def create_checkout_session(
        self,
        *,
        billing_plan_id: int,
        customer_email: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        data = self._post(
            "stripe.createCheckoutSession",
            {
                "billingPlanId": int(billing_plan_id),
                "customerEmail": customer_email,
                "successUrl": success_url,
                "cancelUrl": cancel_url,
            },
        )
        return data if isinstance(data, dict) else {}

    def get_checkout_result(self, session_id: str, *, email: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"sessionId": session_id}
        if email:
            payload["email"] = email
        data = self._get("stripe.getCheckoutResult", payload)
        return data if isinstance(data, dict) else {}

    def get_license_billing(self, *, license_key: str, customer_email: str) -> dict[str, Any]:
        data = self._get(
            "stripe.getLicenseBilling",
            {"licenseKey": license_key, "customerEmail": customer_email},
        )
        return data if isinstance(data, dict) else {}

    def create_customer_portal_session(
        self,
        *,
        license_key: str,
        customer_email: str,
        return_url: str,
    ) -> dict[str, Any]:
        data = self._post(
            "stripe.createCustomerPortalSession",
            {
                "licenseKey": license_key,
                "customerEmail": customer_email,
                "returnUrl": return_url,
            },
        )
        return data if isinstance(data, dict) else {}

    def cancel_subscription(
        self,
        *,
        license_key: str,
        customer_email: str,
        cancel_at_period_end: bool = True,
    ) -> dict[str, Any]:
        data = self._post(
            "stripe.cancelSubscription",
            {
                "licenseKey": license_key,
                "customerEmail": customer_email,
                "cancelAtPeriodEnd": cancel_at_period_end,
            },
        )
        return data if isinstance(data, dict) else {}

    def activate(self, license_key: Optional[str] = None) -> dict[str, Any]:
        key = license_key or self.license_key
        if not key:
            raise ValueError("License key is required for activation")

        device_info = json.dumps(
            {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "machine": platform.machine(),
                "hostname": platform.node(),
                "product": "AnomalyMatrix",
            }
        )
        data = self._post(
            "api.activate",
            {
                "licenseKey": key,
                "deviceId": self.get_device_id(),
                "deviceInfo": device_info,
            },
        )
        if data.get("success"):
            token = data["token"]
            self._token = token
            self._save_token(token)
            self.license_key = key
            return {
                "success": True,
                "token": token,
                "message": data.get("message", "Activation successful"),
            }
        return {"success": False, "message": data.get("message", "Activation failed")}

    def validate(self, online: bool = True) -> dict[str, Any]:
        if not self.token:
            return {"valid": False, "message": "No license token found. Please activate first."}
        if online:
            return self._validate_online()
        return self._validate_offline()

    def _validate_online(self) -> dict[str, Any]:
        try:
            data = self._post("api.validate", {"token": self.token})
            return data or {"valid": False, "message": "Invalid response from server"}
        except LicensingApiError as exc:
            if exc.code == "NETWORK_ERROR":
                offline = self._validate_offline()
                offline["network_error"] = exc.message
                return offline
            raise

    def _validate_offline(self) -> dict[str, Any]:
        try:
            decoded = jwt.decode(self.token, options={"verify_signature": False})
            exp = decoded.get("exp")
            if exp and datetime.fromtimestamp(int(exp), tz=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "valid": False,
                    "offline": True,
                    "message": "License token has expired. Please connect to renew.",
                }
            return {
                "valid": True,
                "offline": True,
                "license": {
                    "productId": decoded.get("productId"),
                    "features": decoded.get("features", []),
                    "expiresAt": datetime.fromtimestamp(int(exp), tz=timezone.utc).isoformat()
                    if exp
                    else None,
                },
            }
        except Exception as exc:  # noqa: BLE001 — surface as validation failure
            return {"valid": False, "offline": True, "message": f"Offline validation failed: {exc}"}

    def deactivate(self) -> dict[str, Any]:
        if not self.license_key:
            raise ValueError("License key is required for deactivation")
        data = self._post(
            "api.deactivate",
            {"licenseKey": self.license_key, "deviceId": self.get_device_id()},
        )
        self._token = None
        if self._token_file.exists():
            self._token_file.unlink()
        return data or {"success": False, "message": "Deactivation failed"}

    def is_valid(self, online: bool = True) -> bool:
        return bool(self.validate(online=online).get("valid", False))
