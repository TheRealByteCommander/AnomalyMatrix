from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="AnomalyMatrix OPC-UA Gateway", version="0.2.0")

_last_publish: dict = {}


class PublishRequest(BaseModel):
    endpoint: str = "opc.tcp://localhost:4840"
    payload: dict = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"ok": True, "service": "opcua-gateway", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/publish")
def publish(request: PublishRequest):
    """Accept mapped OPC-UA node payloads; real asyncua transport is a follow-up milestone."""
    global _last_publish
    _last_publish = {
        "endpoint": request.endpoint,
        "payload": request.payload,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "nodes_written": len(request.payload),
    }
    return {
        "published": True,
        "endpoint": request.endpoint,
        "nodes_written": len(request.payload),
        "published_at": _last_publish["published_at"],
    }


@app.get("/last")
def last_publish():
    return _last_publish or {"published": False}
