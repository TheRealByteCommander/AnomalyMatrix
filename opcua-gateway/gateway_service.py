from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from opcua_server import apply_payload, start_opcua_background, stop_opcua_background

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_last_publish: dict = {}


class PublishRequest(BaseModel):
    endpoint: str = "opc.tcp://0.0.0.0:4840/anomalymatrix/server/"
    payload: dict = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI):
    endpoint = os.getenv("OPCUA_SERVER_ENDPOINT", "opc.tcp://0.0.0.0:4840/anomalymatrix/server/")
    if os.getenv("OPCUA_SERVER_ENABLED", "true").strip().lower() in {"1", "true", "yes"}:
        start_opcua_background(endpoint)
        logger.info("Started OPC UA background server")
    yield
    await stop_opcua_background()


app = FastAPI(title="AnomalyMatrix OPC-UA Gateway", version="0.3.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "opcua-gateway",
        "opcua_enabled": os.getenv("OPCUA_SERVER_ENABLED", "true"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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


@app.get("/last")
def last_publish():
    return _last_publish or {"published": False}


@app.get("/nodes")
def current_nodes():
    from opcua_server import NODE_VALUES

    return NODE_VALUES
