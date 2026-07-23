from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from nodes import load_contract
from opcua_server import NODE_VALUES, apply_payload, start_opcua_background, stop_opcua_background
from service_auth import ServiceAuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_last_publish: dict = {}


class PublishRequest(BaseModel):
    endpoint: str = "opc.tcp://0.0.0.0:4840/anomalymatrix/server/"
    payload: dict = Field(default_factory=dict)


class TriggerRequest(BaseModel):
    camera_id: str = "cam-01"
    recipe_id: str = "recipe-default"


@asynccontextmanager
async def lifespan(app: FastAPI):
    endpoint = os.getenv("OPCUA_SERVER_ENDPOINT", "opc.tcp://0.0.0.0:4840/anomalymatrix/server/")
    if os.getenv("OPCUA_SERVER_ENABLED", "true").strip().lower() in {"1", "true", "yes"}:
        start_opcua_background(endpoint)
        logger.info("Started OPC UA server with PLC trigger/stop interface")
    yield
    await stop_opcua_background()


def _app_version() -> str:
    return os.getenv("ANOMALYMATRIX_VERSION", "1.0.0").strip() or "1.0.0"


def _is_production() -> bool:
    return os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() in {"prod", "production"}


_docs = {}
if _is_production():
    _docs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(
    title="AnomalyMatrix OPC-UA Gateway",
    version=_app_version(),
    lifespan=lifespan,
    **_docs,
)
app.add_middleware(ServiceAuthMiddleware)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "opcua-gateway",
        "version": _app_version(),
        "opcua_enabled": os.getenv("OPCUA_SERVER_ENABLED", "true"),
        "api_url": os.getenv("ANOMALYMATRIX_API_URL", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/contract")
def opcua_contract():
    return load_contract()


@app.post("/publish")
def publish(request: PublishRequest):
    global _last_publish
    nodes_written = apply_payload(request.payload)
    _last_publish = {
        "endpoint": request.endpoint,
        "payload": request.payload,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "nodes_written": nodes_written,
        "opcua_transport": "asyncua",
    }
    return {
        "published": True,
        "endpoint": request.endpoint,
        "nodes_written": nodes_written,
        "published_at": _last_publish["published_at"],
        "opcua_transport": "asyncua",
    }


@app.post("/trigger")
async def manual_trigger(body: TriggerRequest):
    """HTTP fallback to simulate PLC trigger (same as ExternalTrigger rising edge)."""
    from plc_bridge import get_plc_bridge

    bridge = get_plc_bridge()
    ok = await bridge.run_method(NODE_VALUES, body.camera_id, body.recipe_id)
    return {"triggered": ok, "camera_id": body.camera_id, "recipe_id": body.recipe_id}


@app.get("/last")
def last_publish():
    return _last_publish or {"published": False}


@app.get("/nodes")
def current_nodes():
    return NODE_VALUES
