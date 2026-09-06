"""End-customer Stripe billing against the Byte Commander license server.

Proxies public stripe.* tRPC procedures via LICENSE_SERVER_URL.
LICENSE_ADMIN_TOKEN is never used here (and must not reach the HMI).
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from .licensing import LicenseManager, _product_id
from .licensing_sdk import LicensingApiError
from .production import is_production


class LicenseBillingError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _allowed_return_origins(request_origin: str | None = None) -> list[str]:
    origins: list[str] = []
    raw = os.getenv("AMX_CORS_ORIGINS", os.getenv("BC_CORS_ORIGINS", "")).strip()
    origins.extend([item.strip().rstrip("/") for item in raw.split(",") if item.strip()])
    if request_origin:
        origins.append(request_origin.strip().rstrip("/"))
    if not is_production():
        origins.extend(
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:4173",
                "http://127.0.0.1:4173",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost",
                "http://127.0.0.1",
            ]
        )
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for origin in origins:
        if origin and origin not in seen:
            seen.add(origin)
            out.append(origin)
    return out


def validate_return_url(url: str, *, request_origin: str | None = None) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        raise LicenseBillingError("BAD_REQUEST", "return URL required", status_code=400)
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise LicenseBillingError("BAD_REQUEST", "return URL must be an absolute http(s) URL", status_code=400)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    allowed = _allowed_return_origins(request_origin)
    if origin.rstrip("/") not in allowed:
        raise LicenseBillingError("BAD_REQUEST", "return URL origin is not allowed", status_code=400)
    return cleaned


def _http_status_for_code(code: str) -> int:
    mapping = {
        "NETWORK_ERROR": 502,
        "BAD_RESPONSE": 502,
        "PRECONDITION_FAILED": 503,
        "NOT_FOUND": 404,
        "FORBIDDEN": 403,
        "UNAUTHORIZED": 401,
        "TOO_MANY_REQUESTS": 429,
        "BAD_REQUEST": 400,
    }
    return mapping.get(str(code), 502)


class LicenseBillingService:
    def __init__(self, manager: LicenseManager):
        self.manager = manager

    def _require_server(self) -> None:
        if not self.manager.server_configured:
            raise LicenseBillingError(
                "LICENSE_SERVER_UNCONFIGURED",
                "LICENSE_SERVER_URL and LICENSE_PRODUCT_ID are required for billing",
                status_code=503,
            )

    def _client(self) -> LicenseClient:
        self._require_server()
        return self.manager._client(license_key=self.manager.stored_license_key())

    def _call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except LicensingApiError as exc:
            raise LicenseBillingError(
                exc.code,
                exc.message,
                status_code=_http_status_for_code(exc.code),
            ) from exc

    def list_plans(self) -> list[dict]:
        plans = self._call(self._client().list_public_plans)
        pid = _product_id()
        if pid is None:
            return plans
        return [plan for plan in plans if int(plan.get("productId") or 0) == pid]

    def create_checkout(
        self,
        *,
        billing_plan_id: int,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        request_origin: str | None = None,
    ) -> dict:
        if int(billing_plan_id) <= 0:
            raise LicenseBillingError("BAD_REQUEST", "billing_plan_id required", status_code=400)
        email = _require_email(customer_email)
        success = validate_return_url(success_url, request_origin=request_origin)
        cancel = validate_return_url(cancel_url, request_origin=request_origin)
        self.manager.remember_customer_email(email)
        return self._call(
            self._client().create_checkout_session,
            billing_plan_id=billing_plan_id,
            customer_email=email,
            success_url=success,
            cancel_url=cancel,
        )

    def complete_checkout(self, *, session_id: str, customer_email: str | None = None) -> dict:
        session_id = (session_id or "").strip()
        if not session_id:
            raise LicenseBillingError("BAD_REQUEST", "session_id required", status_code=400)
        email = (customer_email or self.manager.stored_customer_email() or "").strip().lower() or None
        result = self._call(self._client().get_checkout_result, session_id, email=email)
        if not isinstance(result, dict):
            raise LicenseBillingError("BAD_RESPONSE", "Invalid checkout result", status_code=502)

        license_key = str(result.get("licenseKey") or "").strip()
        result_email = str(result.get("customerEmail") or email or "").strip().lower()
        if result_email:
            self.manager.remember_customer_email(result_email)

        activated = False
        license_status = None
        if result.get("readyToActivate") and license_key:
            try:
                license_status = self.manager.activate(license_key)
                activated = True
                if result_email:
                    self.manager.remember_customer_email(result_email)
            except PermissionError as exc:
                raise LicenseBillingError("ACTIVATION_FAILED", str(exc), status_code=402) from exc
            except ValueError as exc:
                raise LicenseBillingError("BAD_REQUEST", str(exc), status_code=400) from exc

        return {
            "status": result.get("status"),
            "readyToActivate": bool(result.get("readyToActivate")),
            "activated": activated,
            "sessionId": result.get("sessionId") or session_id,
            "productId": result.get("productId"),
            "productName": result.get("productName"),
            "billingModel": result.get("billingModel"),
            "licenseType": result.get("licenseType"),
            "expiresAt": result.get("expiresAt"),
            "features": result.get("features") or [],
            "license": license_status,
            "license_key_masked": f"***{license_key[-4:]}" if len(license_key) >= 4 else None,
        }

    def get_billing(self, *, customer_email: str | None = None) -> dict:
        key, email = self._credentials(customer_email)
        billing = self._call(self._client().get_license_billing, license_key=key, customer_email=email)
        self.manager.remember_customer_email(email)
        return {
            "available": True,
            "license_key_masked": f"***{key[-4:]}" if len(key) >= 4 else None,
            "productId": billing.get("productId"),
            "status": billing.get("status"),
            "expiresAt": billing.get("expiresAt"),
            "features": billing.get("features") or [],
            "hasStripeSubscription": bool(billing.get("hasStripeSubscription")),
            "subscriptionStatus": billing.get("subscriptionStatus"),
            "cancelAtPeriodEnd": bool(billing.get("cancelAtPeriodEnd")),
            "canCancel": bool(billing.get("canCancel")),
            "canOpenPortal": bool(billing.get("canOpenPortal")),
        }

    def create_portal(self, *, customer_email: str | None = None, return_url: str, request_origin: str | None = None) -> dict:
        key, email = self._credentials(customer_email)
        safe_return = validate_return_url(return_url, request_origin=request_origin)
        result = self._call(
            self._client().create_customer_portal_session,
            license_key=key,
            customer_email=email,
            return_url=safe_return,
        )
        url = result.get("url") if isinstance(result, dict) else None
        if not url:
            raise LicenseBillingError("BAD_RESPONSE", "Customer portal URL missing", status_code=502)
        return {"url": url}

    def cancel(self, *, customer_email: str | None = None, cancel_at_period_end: bool = True) -> dict:
        key, email = self._credentials(customer_email)
        result = self._call(
            self._client().cancel_subscription,
            license_key=key,
            customer_email=email,
            cancel_at_period_end=cancel_at_period_end,
        )
        license_status = self.manager.validate_once()
        return {
            "success": bool(result.get("success")),
            "cancelAtPeriodEnd": bool(result.get("cancelAtPeriodEnd", cancel_at_period_end)),
            "status": result.get("status"),
            "expiresAt": result.get("expiresAt"),
            "license": license_status,
        }

    def _credentials(self, customer_email: str | None) -> tuple[str, str]:
        self._require_server()
        key = self.manager.stored_license_key()
        if not key:
            raise LicenseBillingError(
                "LICENSE_NOT_ACTIVATED",
                "No license key on this device — purchase or activate first",
                status_code=409,
            )
        email = _require_email(customer_email or self.manager.stored_customer_email() or "")
        return key, email


def _require_email(value: str) -> str:
    email = (value or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise LicenseBillingError("BAD_REQUEST", "valid customer email required", status_code=400)
    return email
