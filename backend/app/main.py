from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.health import router as health_router
from .contracts.envelope import error_envelope, success_envelope
from .contracts import events as event_contracts
from .models import CaptureRequest, InferRequest, RunInspectionRequest
from .repository import ResultRepository
from .services_ai import infer_stub
from .services_edge import generate_synthetic_frame

app = FastAPI(
    title="AnomalyMatrix API",
    version="0.2.0",
    description="MVP phase-2 vertical flow scaffold",
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
repo = ResultRepository(Path(__file__).resolve().parents[1] / "data")


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


@app.post("/api/v1/edge/capture")
async def edge_capture(payload: CaptureRequest, request: Request):
    request_id = request.state.request_id
    frame = generate_synthetic_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    return success_envelope(frame.__dict__, request_id)


@app.post("/api/v1/ai/infer")
async def ai_infer(payload: InferRequest, request: Request):
    request_id = request.state.request_id
    inference = infer_stub(payload.model_dump())
    return success_envelope(inference, request_id)


@app.post("/api/v1/orchestrate/run-inspection")
@app.post("/api/v1/inspections/run")
async def run_inspection(request: Request, payload: RunInspectionRequest = Body(default_factory=RunInspectionRequest)):
    request_id = request.state.request_id

    frame = generate_synthetic_frame(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
    inference = infer_stub(frame.__dict__)

    decision = 'red' if inference['anomaly_score'] >= 0.85 else ('amber' if inference['anomaly_score'] >= 0.55 else 'green')
    result = {
        "inspection_id": str(uuid4()),
        "frame": frame.__dict__,
        "inference": inference,
        "decision": decision,
        "heatmap": {"uri": inference['heatmap_uri'], "placeholder": True},
    }
    repo.append(result)

    return success_envelope(result, request_id)


@app.get("/api/v1/results/latest")
@app.get("/api/v1/inspections/recent")
async def results_latest(request: Request, limit: int = 20):
    request_id = request.state.request_id
    data = repo.latest(limit=max(1, min(100, limit)))
    key = "items"
    return success_envelope({key: data, "count": len(data)}, request_id)
