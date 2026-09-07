"""Authenticated HMI endpoints for end-customer license purchase / billing."""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request

from ..contracts.envelope import success_envelope
from ..license_billing import LicenseBillingError, LicenseBillingService
from ..rbac import require_permission, resolve_auth

router = APIRouter(tags=["license-billing"])


def _manager(request: Request):
    from .. import main as main_module

    return main_module.license_manager


def _service(request: Request) -> LicenseBillingService:
    return LicenseBillingService(_manager(request))


def _guard(request: Request, permission: str) -> None:
    from .. import main as main_module

    auth = resolve_auth(request, main_module.core_store)
    request.state.auth = auth
    require_permission(auth, permission)


def _origin(request: Request) -> str | None:
    origin = (request.headers.get("origin") or "").strip()
    if origin:
        return origin
    referer = (request.headers.get("referer") or "").strip()
    if not referer:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(referer)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return None


def _raise(exc: LicenseBillingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/license/plans")
async def license_plans(request: Request):
    _guard(request, "license.read")
    try:
        plans = _service(request).list_plans()
    except LicenseBillingError as exc:
        _raise(exc)
    return success_envelope({"items": plans, "count": len(plans)}, request.state.request_id)


@router.post("/license/checkout")
async def license_checkout(request: Request, payload: dict = Body(...)):
    _guard(request, "license.admin")
    try:
        result = _service(request).create_checkout(
            billing_plan_id=int(payload.get("billing_plan_id") or payload.get("billingPlanId") or 0),
            customer_email=str(payload.get("customer_email") or payload.get("customerEmail") or ""),
            success_url=str(payload.get("success_url") or payload.get("successUrl") or ""),
            cancel_url=str(payload.get("cancel_url") or payload.get("cancelUrl") or ""),
            request_origin=_origin(request),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="billing_plan_id must be an integer") from exc
    except LicenseBillingError as exc:
        _raise(exc)
    return success_envelope(
        {
            "sessionId": result.get("sessionId"),
            "url": result.get("url"),
            "billingModel": result.get("billingModel"),
        },
        request.state.request_id,
    )


@router.get("/license/checkout/result")
async def license_checkout_result(
    request: Request,
    session_id: str = Query(..., min_length=1),
    customer_email: str | None = Query(default=None),
):
    _guard(request, "license.admin")
    try:
        result = _service(request).complete_checkout(
            session_id=session_id,
            customer_email=customer_email,
        )
    except LicenseBillingError as exc:
        _raise(exc)
    return success_envelope(result, request.state.request_id)


@router.get("/license/billing")
async def license_billing(request: Request, customer_email: str | None = Query(default=None)):
    _guard(request, "license.read")
    try:
        result = _service(request).get_billing(customer_email=customer_email)
    except LicenseBillingError as exc:
        _raise(exc)
    # Never leak the raw license key to the HMI.
    result = dict(result)
    result.pop("licenseKey", None)
    return success_envelope(result, request.state.request_id)


@router.post("/license/billing/portal")
async def license_billing_portal(request: Request, payload: dict = Body(default=None)):
    _guard(request, "license.admin")
    body = payload or {}
    try:
        result = _service(request).create_portal(
            customer_email=str(body.get("customer_email") or body.get("customerEmail") or "") or None,
            return_url=str(body.get("return_url") or body.get("returnUrl") or ""),
            request_origin=_origin(request),
        )
    except LicenseBillingError as exc:
        _raise(exc)
    return success_envelope(result, request.state.request_id)


@router.post("/license/billing/cancel")
async def license_billing_cancel(request: Request, payload: dict = Body(default=None)):
    _guard(request, "license.admin")
    body = payload or {}
    cancel_at_period_end = body.get("cancel_at_period_end", body.get("cancelAtPeriodEnd", True))
    try:
        result = _service(request).cancel(
            customer_email=str(body.get("customer_email") or body.get("customerEmail") or "") or None,
            cancel_at_period_end=bool(cancel_at_period_end),
        )
    except LicenseBillingError as exc:
        _raise(exc)
    return success_envelope(result, request.state.request_id)
