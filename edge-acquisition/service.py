from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from camera_drivers import encode_image_b64, get_camera_driver
from service_auth import ServiceAuthMiddleware

app = FastAPI(title="AnomalyMatrix Edge Acquisition", version="1.0.0")
app.add_middleware(ServiceAuthMiddleware)


class CaptureRequest(BaseModel):
    camera_id: str = "cam-01"
    recipe_id: str = "recipe-default"


@app.get("/health")
def health():
    return {"ok": True, "service": "edge-acquisition", "version": "1.0.0"}


@app.post("/capture")
def capture(payload: CaptureRequest):
    frame_id = str(uuid4())
    driver = get_camera_driver()
    try:
        image, meta = driver.capture(camera_id=payload.camera_id, recipe_id=payload.recipe_id)
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
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Capture failed") from exc
