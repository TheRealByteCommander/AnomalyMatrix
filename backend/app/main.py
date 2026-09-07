from __future__ import annotations

import asyncio
import contextlib
import json
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
from .api.health import app_version, router as health_router
from .api.license_billing import router as license_billing_router
from .api.training import router as training_router
from .camera_station import MAX_CAMERAS, MIN_CAMERAS, CameraSelectionError, CameraStationStore
from .contracts.envelope import error_envelope, success_envelope
from .contracts import events as event_contracts
from .core_store import CoreStore
from .event_bus import DomainEventBus
from .heatmap import generate_heatmap_png
from .inference_provider import _frame_grayscale, get_inference_provider
from .licensing import LicenseManager
from .metrics_influx import query_observability_summary, record_inspection_metrics, record_process_trend
from .middleware_production import configure_production_middleware
from .models import CameraSelectionRequest, CaptureRequest, InferRequest, RunInspectionRequest
from .opcua_publish import publish_busy_state, publish_to_opcua
from .production import enforce_production_config, is_production
from .rbac import require_permission, resolve_auth
from .repository_factory import build_repository
from .services_edge import capture_frame, frame_to_dict, list_edge_cameras
from .storage_minio import ensure_buckets, store_heatmap_binary, store_raw_frame
from .trend_warnings import maybe_emit_trend_warning

_data_root = Path(__file__).resolve().parents[1] / "data"
_dsn = os.getenv("DATABASE_URL", "").strip() or None
repo = build_repository(_data_root)
core_store = CoreStore(_data_root, dsn=_dsn)
license_manager = LicenseManager()
event_bus = DomainEventBus(_data_root)
camera_station = CameraStationStore(_data_root / "station_cameras.json")

_DECISION_RANK = {"green": 0, "amber": 1, "red": 2}


def _score_to_decision(score: float) -> str:
    if score >= 0.85:
        return "red"
    if score >= 0.55:
        return "amber"
    return "green"


def _resolve_run_cameras(payload: RunInspectionRequest) -> tuple[list[str], dict[str, str]]:
    """Priority: camera_ids → single camera_id → station selection → cam-01."""
    selection = camera_station.load()
    sources = dict(selection.get("sources") or {})
    if payload.camera_ids:
        return list(payload.camera_ids), sources
    if payload.camera_id:
        return [payload.camera_id], sources
    if selection.get("camera_ids"):
        return list(selection["camera_ids"]), sources
    return ["cam-01"], sources


def _run_single_view(
    *,
    inspection_id: str,
    camera_id: str,
    recipe_id: str,
    source: str | None,
    provider,
) -> dict:
    frame = capture_frame(camera_id=camera_id, recipe_id=recipe_id, source=source)
    frame_dict = frame_to_dict(frame)
    inference = provider.infer(frame_dict)
    decision = _score_to_decision(float(inference.anomaly_score))
    view = {
        "camera_id": camera_id,
        "source": source or frame_dict.get("source"),
        "frame": frame_dict,
        "inference": inference.__dict__,
        "decision": decision,
        "heatmap": {"uri": inference.heatmap_uri, "placeholder": False},
    }

    gray = _frame_grayscale(frame_dict)
    heatmap_png = generate_heatmap_png(gray, inference.anomaly_score)
    if frame_dict.get("image_b64"):
        import base64

        try:
            raw_bytes = base64.b64decode(frame_dict["image_b64"])
            raw_uri = store_raw_frame(
                inspection_id=inspection_id,
                recipe_id=recipe_id,
                image_bytes=raw_bytes,
                camera_id=camera_id,
            )
            if raw_uri:
                view["frame"]["stored_raw_uri"] = raw_uri
        except Exception:
            pass

    stored_uri = store_heatmap_binary(
        inspection_id=inspection_id,
        png_bytes=heatmap_png,
        anomaly_score=inference.anomaly_score,
        camera_id=camera_id,
    )
    if stored_uri:
        view["heatmap"] = {"uri": stored_uri, "placeholder": False, "storage": "minio"}
    return view



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
            # Seed migration may leave 'dev-placeholder' — treat as unset.
            # Never overwrite a real password on container restart.
            needs_bootstrap = (not stored) or stored == "dev-placeholder"
            if needs_bootstrap:
                if core_store.set_user_password("admin-1", admin_pw):
                    logger.info("Admin password bootstrapped from AMX_ADMIN_PASSWORD")
                else:
                    logger.warning("Failed to bootstrap admin-1 password")
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


_docs_kwargs = {}
if is_production():
    _docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(
    title="AnomalyMatrix API",
    version=app_version(),
    description="v1.2.0: Production-ready inspection platform (multi-camera, drift, license server)",
    lifespan=lifespan,
    **_docs_kwargs,
)

configure_production_middleware(app)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(license_billing_router, prefix="/api/v1")


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
    # license.admin must NOT be feature-gated — otherwise activate is impossible
    # on a fresh enforced install.
    license_map = {
        "inspection.run": "inspection.run",
        "inspection.read": "inspection.read",
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
    features = getattr(snap, "enabled_features", None)
    if features is None:
        raw = getattr(snap, "features", [])
        features = list(raw.keys()) if isinstance(raw, dict) else list(raw or [])
    payload = {
        "active": bool(getattr(snap, "active", False)),
        "tier": getattr(snap, "tier", "none"),
        "features": features,
        "token_present": bool(getattr(snap, "token_present", False)),
        "valid_until": getattr(snap, "valid_until", None),
        "last_validation_at": getattr(snap, "last_validation_at", None),
        "offline_grace_until": getattr(snap, "offline_grace_until", None),
        "grace_active": bool(getattr(snap, "grace_active", False)),
        "mode": "server" if license_manager.server_configured else "local",
        "last_error": getattr(snap, "last_error", None) if not is_production() else None,
    }
    payload.update(license_manager.billing_hints())
    return success_envelope(payload, request_id)


@app.post("/api/v1/license/activate")
async def license_activate(request: Request, payload: dict = Body(...)):
    _guard(request, "license.admin")
    _check_admin_token(request)
    request_id = request.state.request_id
    key = str(payload.get("license_key", "")).strip()
    if not key:
        raise HTTPException(status_code=400, detail="license_key required")
    try:
        state = license_manager.activate(key)
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_envelope(
        {
            "active": state.get("active", False),
            "tier": state.get("tier"),
            "features": state.get("features", []),
            "mode": state.get("mode"),
        },
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
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "inspection_result_v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}
    return success_envelope(
        {
            "schema_version": schema.get("version") or "1.2.0",
            "schema": schema,
            "fields": [
                "inspection_id",
                "frame",
                "inference",
                "decision",
                "heatmap",
                "camera_ids",
                "view_count",
                "views",
                "decision_policy",
                "worst_view_camera_id",
                "trend_warning",
                "by_camera",
                "drifting_camera_id",
                "opcua_publish",
                "license_tier",
            ],
            "notes": {
                "frame_inference_heatmap": "Worst-view projection for backward compatibility",
                "decision_policy": "worst_view",
                "by_camera": "Per-camera drift / trend breakdown",
            },
        },
        request_id,
    )


@app.post("/api/v1/edge/capture")
async def edge_capture(payload: CaptureRequest, request: Request):
    _guard(request, "inspection.run")
    request_id = request.state.request_id
    frame = capture_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id, source=payload.source)
    return success_envelope(frame_to_dict(frame), request_id)


@app.get("/api/v1/cameras")
async def cameras_list(request: Request):
    _guard(request, "cameras.read")
    request_id = request.state.request_id
    discovered = list_edge_cameras()
    selection = camera_station.load()
    selected = set(selection.get("camera_ids") or [])
    cameras = []
    for cam in discovered.get("cameras") or []:
        item = dict(cam)
        item["selected"] = item.get("camera_id") in selected
        cameras.append(item)
    return success_envelope(
        {
            "cameras": cameras,
            "driver": discovered.get("driver"),
            "host": discovered.get("host"),
            "min_selectable": MIN_CAMERAS,
            "max_selectable": MAX_CAMERAS,
            "selection": selection,
        },
        request_id,
    )


@app.get("/api/v1/cameras/selection")
async def cameras_selection_get(request: Request):
    _guard(request, "cameras.read")
    request_id = request.state.request_id
    return success_envelope(camera_station.load(), request_id)


@app.put("/api/v1/cameras/selection")
async def cameras_selection_put(request: Request, payload: CameraSelectionRequest):
    _guard(request, "cameras.configure")
    request_id = request.state.request_id
    discovered = list_edge_cameras()
    available = {
        str(c.get("camera_id")): c
        for c in (discovered.get("cameras") or [])
        if c.get("camera_id") and c.get("available", True)
    }
    sources = {
        cid: str(available[cid].get("source") or cid)
        for cid in payload.camera_ids
        if cid in available
    }
    try:
        saved = camera_station.save(
            camera_ids=payload.camera_ids,
            sources=sources,
            available_ids=set(available.keys()),
        )
    except CameraSelectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    auth = request.state.auth
    core_store.append_audit(
        actor=auth.user_id,
        action="cameras.configure",
        resource_type="camera_station",
        resource_id="default",
        after_state={"camera_ids": saved["camera_ids"]},
        request_id=request_id,
    )
    return success_envelope(saved, request_id)


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

    camera_ids, sources = _resolve_run_cameras(payload)
    primary_camera = camera_ids[0]
    publish_busy_state(camera_id=primary_camera, recipe_id=payload.recipe_id)

    try:
        inspection_id = str(uuid4())
        provider = get_inference_provider()
        views: list[dict] = []
        for camera_id in camera_ids:
            view = _run_single_view(
                inspection_id=inspection_id,
                camera_id=camera_id,
                recipe_id=payload.recipe_id,
                source=sources.get(camera_id),
                provider=provider,
            )
            views.append(view)

        # Aggregate: worst-view wins (highest anomaly severity)
        primary = max(
            views,
            key=lambda v: (
                _DECISION_RANK.get(v["decision"], 0),
                float(v["inference"].get("anomaly_score", 0.0)),
            ),
        )
        decision = primary["decision"]
        snap = license_manager.snapshot()
        result = {
            "inspection_id": inspection_id,
            "frame": primary["frame"],
            "inference": primary["inference"],
            "decision": decision,
            "heatmap": primary["heatmap"],
            "license_tier": snap.tier,
            "camera_ids": camera_ids,
            "view_count": len(views),
            "views": views,
            "decision_policy": "worst_view",
            "worst_view_camera_id": primary.get("camera_id"),
        }

        # Trend enrichment BEFORE persist/OPC-UA so interfaces stay consistent
        from .trend_warnings import enrich_trend_summary

        prior = list(reversed(repo.latest(limit=49)))
        window_items = prior + [result]
        scores = [float(i.get("inference", {}).get("anomaly_score", 0.0)) for i in window_items]
        trend = enrich_trend_summary(
            {
                "count": len(window_items),
                "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                "max_score": round(max(scores), 4) if scores else 0.0,
                "anomaly_count": sum(
                    1 for i in window_items if i.get("inference", {}).get("status") == "anomaly"
                ),
            },
            window_items,
        )

        result["trend_warning"] = bool(trend.get("trend_warning", False))
        result["trend_severity"] = trend.get("trend_severity", "green")
        result["trend_reason"] = trend.get("trend_reason")
        result["by_camera"] = trend.get("by_camera") or []
        result["drifting_camera_id"] = trend.get("drifting_camera_id")
        result["drifting_cameras"] = trend.get("drifting_cameras") or []
        result["score_delta"] = trend.get("score_delta")
        result["drift_score"] = trend.get("drift_score")
        result["baseline_avg_score"] = trend.get("baseline_avg_score")

        opcua = publish_to_opcua(result)
        result["opcua_publish"] = opcua.__dict__

        latency_ms = (time.perf_counter() - started) * 1000.0
        record_inspection_metrics(
            inspection_id=inspection_id,
            score=float(primary["inference"].get("anomaly_score", 0.0)),
            latency_ms=latency_ms,
            decision=decision,
            provider=primary["inference"].get("provider"),
            opcua_published=bool(opcua.published),
        )
        event = _event_bus(request).emit_inspection_completed(result, latency_ms=latency_ms)
        result["domain_event_id"] = event.get("event_id")

        repo.append(result)
        record_process_trend(avg_score=float(trend.get("avg_score", primary["inference"].get("anomaly_score", 0.0))))
        trend_event = maybe_emit_trend_warning(
            _event_bus(request),
            trend=trend,
            recipe_id=payload.recipe_id,
            model_version=primary["inference"].get("model_version"),
        )
        if trend_event:
            result["trend_warning_event_id"] = trend_event.get("event_id")

        core_store.append_audit(
            actor=auth.user_id,
            action="inspection.run",
            resource_type="inspection",
            resource_id=inspection_id,
            after_state={
                "decision": decision,
                "score": primary["inference"].get("anomaly_score"),
                "camera_ids": camera_ids,
                "view_count": len(views),
                "worst_view_camera_id": primary.get("camera_id"),
                "drifting_camera_id": result.get("drifting_camera_id"),
            },
            request_id=request.state.request_id,
        )
        return success_envelope(result, request_id)
    except Exception:
        # Never leave PLC Busy=true if capture/inference fails after busy publish.
        try:
            from .opcua_nodes import node
            from .opcua_publish import publish_opcua_payload

            publish_opcua_payload(
                {
                    node("inspection.busy"): False,
                    node("inspection.result_ready"): False,
                    node("system_state"): "error",
                }
            )
        except Exception:
            pass
        raise


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
    camera_id: str | None = None,
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    max_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
):
    _guard(request, "inspection.read")
    request_id = request.state.request_id
    data = repo.query(
        recipe_id=recipe_id,
        camera_id=camera_id,
        min_score=min_score,
        max_score=max_score,
        limit=limit,
    )
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
        "by_camera": trend.get("by_camera") or [],
        "drifting_camera_id": trend.get("drifting_camera_id"),
        "drifting_cameras": trend.get("drifting_cameras") or [],
        "score_delta": trend.get("score_delta"),
        "drift_score": trend.get("drift_score"),
        "baseline_avg_score": trend.get("baseline_avg_score"),
        "camera_count": trend.get("camera_count", 0),
        "view_sample_count": trend.get("view_sample_count", 0),
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
