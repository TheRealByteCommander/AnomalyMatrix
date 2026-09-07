from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from camera_discover import discover_cameras
from camera_drivers import encode_image_b64, get_camera_driver
from service_auth import ServiceAuthMiddleware


def _app_version() -> str:
    return os.getenv("ANOMALYMATRIX_VERSION", "1.2.0").strip() or "1.2.0"


def _is_production() -> bool:
    return os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() in {"prod", "production"}


_docs = {}
if _is_production():
    _docs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(
    title="AnomalyMatrix Edge Acquisition",
    version=_app_version(),
    **_docs,
)
app.add_middleware(ServiceAuthMiddleware)


class CaptureRequest(BaseModel):
    camera_id: str = "cam-01"
    recipe_id: str = "recipe-default"
    source: str | None = Field(
        default=None,
        description="Optional device override (index/path, GigE serial, user name, or GenTL id)",
    )


@app.get("/health")
def health():
    return {"ok": True, "service": "edge-acquisition", "version": _app_version()}


@app.get("/cameras")
def cameras():
    """List hardware-detected (or synthetic) cameras available for selection."""
    return discover_cameras()


@app.post("/capture")
def capture(payload: CaptureRequest):
    frame_id = str(uuid4())
    driver = get_camera_driver()
    try:
        image, meta = driver.capture(
            camera_id=payload.camera_id,
            recipe_id=payload.recipe_id,
            source=payload.source,
        )
        image_b64 = encode_image_b64(image)
        return {
            "frame_id": frame_id,
            "camera_id": payload.camera_id,
            "recipe_id": payload.recipe_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "image_uri": f"capture://frame/{frame_id}.png",
            "image_b64": image_b64,
            "image_width": int(image.shape[1]),
            "image_height": int(image.shape[0]),
            "exposure_ms": float(meta.get("exposure_ms", 10.0)),
            "gain_db": float(meta.get("gain_db", 0.0)),
            "capture_driver": meta.get("driver", "unknown"),
            "source": meta.get("source"),
            "trigger_mode": meta.get("trigger_mode"),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc) or "Capture failed") from exc
