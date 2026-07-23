from __future__ import annotations

import asyncio
import contextlib
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.auth import router as auth_router
from .api.catalog import router as catalog_router
from .api.health import router as health_router
from .api.training import router as training_router
from .contracts.envelope import error_envelope, success_envelope
from .contracts import events as event_contracts
from .core_store import CoreStore
from .event_bus import DomainEventBus
from .heatmap import generate_heatmap_png
from .inference_provider import _frame_grayscale, get_inference_provider
from .licensing import LicenseManager
from .metrics_influx import query_observability_summary, record_inspection_metrics, record_process_trend
from .middleware_production import configure_production_middleware
from .models import CaptureRequest, InferRequest, RunInspectionRequest
from .opcua_publish import publish_busy_state, publish_to_opcua
from .production import enforce_production_config, is_production
from .rbac import require_permission, resolve_auth
from .repository_factory import build_repository
from .services_edge import capture_frame, frame_to_dict
from .storage_minio import ensure_buckets, store_heatmap_binary, store_raw_frame
from .trend_warnings import maybe_emit_trend_warning

_data_root = Path(__file__).resolve().parents[1] / "data"
_dsn = os.getenv("DATABASE_URL", "").strip() or None
repo = build_repository(_data_root)
core_store = CoreStore(_data_root, dsn=_dsn)
license_manager = LicenseManager()
event_bus = DomainEventBus(_data_root)


@asynccontextmanager
async def lifespan(app: FastAPI):
    enforce_production_config()
    app.state.core_store = core_store
    app.state.event_bus = event_bus
    if is_production():
        import logging

        logger = logging.getLogger(__name__)
        admin_pw = os.getenv("AMX_ADMIN_PASSWORD", "").strip()
        if admin_pw:
            user = core_store.get_user_by_id("admin-1") or {}
            stored = str(user.get("password_hash") or "").strip()
            force = os.getenv("AMX_BOOTSTRAP_FORCE", "").strip().lower() in {"1", "true", "yes"}
            # Seed migration may leave 'dev-placeholder' — treat as unset
            needs_bootstrap = force or (not stored) or stored == "dev-placeholder"
            if needs_bootstrap:
                if core_store.set_user_password("admin-1", admin_pw):
                    logger.info("Admin password bootstrapped from AMX_ADMIN_PASSWORD")
                else:
                    logger.warning("Failed to bootstrap admin-1 password")
            else:
                logger.info("Admin password already set — skip bootstrap (set AMX_BOOTSTRAP_FORCE=true to overwrite)")
        elif not (core_store.get_user_by_id("admin-1") or {}).get("password_hash"):
            logger.warning("Production: set AMX_ADMIN_PASSWORD or configure admin-1 password_hash in database")
    license_manager.validate_once()
    ensure_buckets()

    stop = False

    async def validator_loop():
        while not stop:
            await asyncio.sleep(license_manager.validation_interval_sec)
            license_manager.validate_once()

    task = asyncio.create_task(validator_loop())
    try:
        yield
    finally:
        stop = True
        task.cancel()
        with contextlib.suppress(BaseException):
            await task


app = FastAPI(
    title="AnomalyMatrix API",
    version="1.0.0",
    description="v1.0: Production-ready inspection platform",
    lifespan=lifespan,
)

configure_production_middleware(app)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")


def _auth(request: Request):
    return resolve_auth(request, core_store)


def _require_license_feature(feature: str):
    try:
        license_manager.enforce_feature(feature)
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


def _guard(request: Request, permission: str) -> None:
    auth = _auth(request)
    request.state.auth = auth
    require_permission(auth, permission)
    license_map = {
        "inspection.run": "inspection.run",
        "inspection.read": "inspection.read",
        "license.admin": "inspection.run",
    }
    lic = license_map.get(permission)
    if lic:
        _require_license_feature(lic)


def _event_bus(_request: Request) -> DomainEventBus:
    return event_bus


def _check_admin_token(request: Request):
    expected = os.getenv("LICENSE_ADMIN_TOKEN", "").strip()
    provided = request.headers.get("X-License-Admin-Token", "").strip()
    # Always require a configured admin token when license admin actions are used.
    if not expected:
        if is_production() or os.getenv("LICENSE_ENFORCE", "").strip().lower() in {"1", "true", "yes"}:
            raise HTTPException(status_code=503, detail="LICENSE_ADMIN_TOKEN not configured")
        return
    import secrets

    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid admin token")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    payload = error_envelope(
        code="HTTP_ERROR",
        message=str(exc.detail),
        request_id=request_id,
        details={"status": exc.status_code},
        retryable=500 <= exc.status_code < 600,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    payload = error_envelope(
        code="HTTP_ERROR",
        message=str(exc.detail),
        request_id=request_id,
        details={"status": exc.status_code},
        retryable=500 <= exc.status_code < 600,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging

    request_id = getattr(request.state, "request_id", str(uuid4()))
    logging.getLogger("anomalymatrix.api").exception(
        "Unhandled exception request_id=%s: %s", request_id, exc
    )
    details = {"status": 500}
    if not is_production():
        details["exception"] = str(exc)
    payload = error_envelope(
        code="INTERNAL_ERROR",
        message="Unexpected backend error",
        request_id=request_id,
        details=details,
        retryable=True,
    )
    return JSONResponse(status_code=500, content=payload)


@app.get("/api/v1/license/status")
async def license_status(request: Request):
    _guard(request, "license.read")
    request_id = request.state.request_id
    snap = license_manager.snapshot()
    payload = {
        "active": bool(getattr(snap, "active", False)),
        "tier": getattr(snap, "tier", "none"),
        "features": list(getattr(snap, "features", [])),
        "token_present": bool(getattr(snap, "token_present", False)),
        "valid_until": getattr(snap, "valid_until", None),
        "last_validation_at": getattr(snap, "last_validation_at", None),
        "offline_grace_until": getattr(snap, "offline_grace_until", None),
        "grace_active": bool(getattr(snap, "grace_active", False)),
        "last_error": getattr(snap, "last_error", None) if not is_production() else None,
    }
    return success_envelope(payload, request_id)


@app.post("/api/v1/license/activate")
async def license_activate(request: Request, payload: dict = Body(...)):
    _guard(request, "license.admin")
    _check_admin_token(request)
    request_id = request.state.request_id
    key = str(payload.get("license_key", "")).strip()
    if not key:
        raise HTTPException(status_code=400, detail="license_key required")
    state = license_manager.activate(key)
    return success_envelope(
        {"active": state.get("active", False), "tier": state.get("tier"), "features": state.get("features", [])},
        request_id,
    )


@app.post("/api/v1/license/deactivate")
async def license_deactivate(request: Request):
    _guard(request, "license.admin")
    _check_admin_token(request)
    request_id = request.state.request_id
    state = license_manager.deactivate()
    return success_envelope({"active": state.get("active", False)}, request_id)


@app.get("/api/v1/contracts/events")
async def contracts_events(request: Request):
    _guard(request, "contracts.read")
    request_id = request.state.request_id
    return success_envelope(
        {
            "InspectionCompleted": event_contracts.InspectionCompleted.model_json_schema(),
            "FeedbackSubmitted": event_contracts.FeedbackSubmitted.model_json_schema(),
            "ModelRetrained": event_contracts.ModelRetrained.model_json_schema(),
            "TrendWarningRaised": event_contracts.TrendWarningRaised.model_json_schema(),
        },
        request_id,
    )


@app.get("/api/v1/contracts/opcua")
async def contracts_opcua(request: Request):
    from .opcua_nodes import load_opcua_contract

    _guard(request, "contracts.read")
    request_id = request.state.request_id
    return success_envelope(load_opcua_contract(), request_id)


@app.get("/api/v1/contracts/inspection-result")
async def contracts_inspection_result(request: Request):
    _guard(request, "contracts.read")
    request_id = request.state.request_id
    return success_envelope(
        {
            "schema_version": "1.1.0",
            "fields": ["inspection_id", "frame", "inference", "decision", "heatmap", "opcua_publish", "license_tier"],
        },
        request_id,
    )


@app.post("/api/v1/edge/capture")
async def edge_capture(payload: CaptureRequest, request: Request):
    _guard(request, "inspection.run")
    request_id = request.state.request_id
    frame = capture_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    return success_envelope(frame_to_dict(frame), request_id)


@app.post("/api/v1/ai/infer")
async def ai_infer(payload: InferRequest, request: Request):
    _guard(request, "inspection.run")
    request_id = request.state.request_id
    provider = get_inference_provider()
    inference = provider.infer(payload.model_dump())
    return success_envelope(inference.__dict__, request_id)


@app.post("/api/v1/orchestrate/run-inspection")
@app.post("/api/v1/inspections/run")
async def run_inspection(request: Request, payload: RunInspectionRequest = Body(default_factory=RunInspectionRequest)):
    _guard(request, "inspection.run")
    auth = request.state.auth
    request_id = request.state.request_id
    started = time.perf_counter()

    publish_busy_state(camera_id=payload.camera_id, recipe_id=payload.recipe_id)

    frame = capture_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    frame_dict = frame_to_dict(frame)
    provider = get_inference_provider()
    inference = provider.infer(frame_dict)

    decision = 'red' if inference.anomaly_score >= 0.85 else ('amber' if inference.anomaly_score >= 0.55 else 'green')
    snap = license_manager.snapshot()
    inspection_id = str(uuid4())
    result = {
        "inspection_id": inspection_id,
        "frame": frame_dict,
        "inference": inference.__dict__,
        "decision": decision,
        "heatmap": {"uri": inference.heatmap_uri, "placeholder": False},
        "license_tier": snap.tier,
    }

    gray = _frame_grayscale(frame_dict)
    heatmap_png = generate_heatmap_png(gray, inference.anomaly_score)
    if frame_dict.get("image_b64"):
        import base64

        try:
            raw_bytes = base64.b64decode(frame_dict["image_b64"])
            raw_uri = store_raw_frame(inspection_id=inspection_id, recipe_id=payload.recipe_id, image_bytes=raw_bytes)
            if raw_uri:
                result["frame"]["stored_raw_uri"] = raw_uri
        except Exception:
            pass

    opcua = publish_to_opcua(result)
    result["opcua_publish"] = opcua.__dict__

    stored_uri = store_heatmap_binary(
        inspection_id=inspection_id,
        png_bytes=heatmap_png,
        anomaly_score=inference.anomaly_score,
    )
    if stored_uri:
        result["heatmap"] = {"uri": stored_uri, "placeholder": False, "storage": "minio"}

    latency_ms = (time.perf_counter() - started) * 1000.0
    record_inspection_metrics(
        inspection_id=inspection_id,
        score=inference.anomaly_score,
        latency_ms=latency_ms,
        decision=decision,
        provider=inference.provider,
        opcua_published=bool(opcua.published),
    )
    event = _event_bus(request).emit_inspection_completed(result, latency_ms=latency_ms)
    result["domain_event_id"] = event.get("event_id")

    repo.append(result)
    trend = repo.trend_summary()
    record_process_trend(avg_score=float(trend.get("avg_score", inference.anomaly_score)))
    result["trend_warning"] = trend.get("trend_warning", False)
    trend_event = maybe_emit_trend_warning(
        _event_bus(request),
        trend=trend,
        recipe_id=frame.recipe_id,
        model_version=inference.model_version,
    )
    if trend_event:
        result["trend_warning_event_id"] = trend_event.get("event_id")

    core_store.append_audit(
        actor=auth.user_id,
        action="inspection.run",
        resource_type="inspection",
        resource_id=inspection_id,
        after_state={"decision": decision, "score": inference.anomaly_score},
        request_id=request.state.request_id,
    )
    return success_envelope(result, request_id)


@app.get("/api/v1/results/latest")
@app.get("/api/v1/inspections/recent")
async def results_latest(request: Request, limit: int = 20):
    _guard(request, "inspection.read")
    request_id = request.state.request_id
    data = repo.latest(limit=max(1, min(100, limit)))
    return success_envelope({"items": data, "count": len(data)}, request_id)


@app.get("/api/v1/results/query")
async def results_query(
    request: Request,
    recipe_id: str | None = None,
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    max_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
):
    _guard(request, "inspection.read")
    request_id = request.state.request_id
    data = repo.query(recipe_id=recipe_id, min_score=min_score, max_score=max_score, limit=limit)
    return success_envelope({"items": data, "count": len(data)}, request_id)


@app.get("/api/v1/results/trend-summary")
async def results_trend_summary(request: Request):
    _guard(request, "trends.read")
    request_id = request.state.request_id
    return success_envelope(repo.trend_summary(), request_id)


@app.get("/api/v1/observability/summary")
async def observability_summary(request: Request):
    _guard(request, "trends.read")
    request_id = request.state.request_id
    trend = repo.trend_summary()
    influx = query_observability_summary()
    payload = {
        "avg_score": trend.get("avg_score", 0.0),
        "max_score": trend.get("max_score", 0.0),
        "inspection_count": trend.get("count", 0),
        "anomaly_count": trend.get("anomaly_count", 0),
        "trend_warning": trend.get("trend_warning", False),
        "trend_severity": trend.get("trend_severity", "green"),
        "trend_reason": trend.get("trend_reason"),
        "inference_p95_ms": influx.get("inference_p95_ms", 0.0),
        "opc_ua_publish_error_rate_pct": influx.get("opc_ua_publish_error_rate_pct", 0.0),
        "metrics_source": influx.get("source", "repository"),
    }
    return success_envelope(payload, request_id)


@app.get("/api/v1/events/recent")
async def events_recent(request: Request, limit: int = Query(default=20, ge=1, le=200)):
    _guard(request, "inspection.read")
    request_id = request.state.request_id
    items = _event_bus(request).recent(limit=limit)
    return success_envelope({"items": items, "count": len(items)}, request_id)
