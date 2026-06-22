from __future__ import annotations

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.health import router as health_router
from .contracts.envelope import error_envelope, success_envelope
from .contracts import events as event_contracts
from .inference_provider import get_inference_provider
from .licensing import LicenseManager
from .models import CaptureRequest, InferRequest, RunInspectionRequest
from .opcua_publish import publish_to_opcua
from .repository_factory import build_repository
from .services_edge import capture_frame, frame_to_dict

repo = build_repository(Path(__file__).resolve().parents[1] / "data")
license_manager = LicenseManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup validation
    license_manager.validate_once()

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
    version="0.4.0",
    description="MVP phase-3 real-path scaffold + licensing",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])


def _require_license_feature(feature: str):
    try:
        license_manager.enforce_feature(feature)
    except PermissionError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


def _check_admin_token(request: Request):
    expected = os.getenv('LICENSE_ADMIN_TOKEN', '').strip()
    provided = request.headers.get('X-License-Admin-Token', '')
    if expected and provided != expected:
        raise HTTPException(status_code=403, detail='Invalid admin token')


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
    request_id = getattr(request.state, "request_id", str(uuid4()))
    payload = error_envelope(
        code="INTERNAL_ERROR",
        message="Unexpected backend error",
        request_id=request_id,
        details={"exception": str(exc)},
        retryable=True,
    )
    return JSONResponse(status_code=500, content=payload)


@app.get("/api/v1/license/status")
async def license_status(request: Request):
    request_id = request.state.request_id
    snap = license_manager.snapshot()
    payload = {
        'active': bool(getattr(snap, 'active', False)),
        'tier': getattr(snap, 'tier', 'none'),
        'features': list(getattr(snap, 'features', [])),
        'token_present': bool(getattr(snap, 'token_present', False)),
        'valid_until': getattr(snap, 'valid_until', None),
        'last_validation_at': getattr(snap, 'last_validation_at', None),
        'offline_grace_until': getattr(snap, 'offline_grace_until', None),
        'grace_active': bool(getattr(snap, 'grace_active', False)),
        'last_error': getattr(snap, 'last_error', None),
    }
    return success_envelope(payload, request_id)


@app.post("/api/v1/license/activate")
async def license_activate(request: Request, payload: dict = Body(...)):
    _check_admin_token(request)
    request_id = request.state.request_id
    key = str(payload.get('license_key', '')).strip()
    if not key:
        raise HTTPException(status_code=400, detail='license_key required')
    state = license_manager.activate(key)
    return success_envelope({'active': state.get('active', False), 'tier': state.get('tier'), 'features': state.get('features', [])}, request_id)


@app.post("/api/v1/license/deactivate")
async def license_deactivate(request: Request):
    _check_admin_token(request)
    request_id = request.state.request_id
    state = license_manager.deactivate()
    return success_envelope({'active': state.get('active', False)}, request_id)


@app.get("/api/v1/contracts/events")
async def contracts_events(request: Request):
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


@app.get("/api/v1/contracts/inspection-result")
async def contracts_inspection_result(request: Request):
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
    _require_license_feature('inspection.run')
    request_id = request.state.request_id
    frame = capture_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    return success_envelope(frame_to_dict(frame), request_id)


@app.post("/api/v1/ai/infer")
async def ai_infer(payload: InferRequest, request: Request):
    _require_license_feature('inspection.run')
    request_id = request.state.request_id
    provider = get_inference_provider()
    inference = provider.infer(payload.model_dump())
    return success_envelope(inference.__dict__, request_id)


@app.post("/api/v1/orchestrate/run-inspection")
@app.post("/api/v1/inspections/run")
async def run_inspection(request: Request, payload: RunInspectionRequest = Body(default_factory=RunInspectionRequest)):
    _require_license_feature('inspection.run')
    request_id = request.state.request_id

    frame = capture_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    provider = get_inference_provider()
    inference = provider.infer(frame_to_dict(frame))

    decision = 'red' if inference.anomaly_score >= 0.85 else ('amber' if inference.anomaly_score >= 0.55 else 'green')
    snap = license_manager.snapshot()
    result = {
        "inspection_id": str(uuid4()),
        "frame": frame_to_dict(frame),
        "inference": inference.__dict__,
        "decision": decision,
        "heatmap": {"uri": inference.heatmap_uri, "placeholder": True},
        "license_tier": snap.tier,
    }

    opcua = publish_to_opcua(result)
    result["opcua_publish"] = opcua.__dict__

    repo.append(result)
    return success_envelope(result, request_id)


@app.get("/api/v1/results/latest")
@app.get("/api/v1/inspections/recent")
async def results_latest(request: Request, limit: int = 20):
    _require_license_feature('inspection.read')
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
    _require_license_feature('inspection.read')
    request_id = request.state.request_id
    data = repo.query(recipe_id=recipe_id, min_score=min_score, max_score=max_score, limit=limit)
    return success_envelope({"items": data, "count": len(data)}, request_id)


@app.get("/api/v1/results/trend-summary")
async def results_trend_summary(request: Request):
    _require_license_feature('inspection.read')
    request_id = request.state.request_id
    return success_envelope(repo.trend_summary(), request_id)
