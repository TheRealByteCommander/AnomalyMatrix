from __future__ import annotations

import logging
import os
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from .production import is_production
from .service_auth import service_auth_headers

logger = logging.getLogger(__name__)


@dataclass
class SyntheticFrame:
    frame_id: str
    camera_id: str
    recipe_id: str
    captured_at: str
    image_uri: str
    exposure_ms: float
    gain_db: float
    image_b64: str | None = None
    image_width: int | None = None
    image_height: int | None = None
    capture_driver: str | None = None


def frame_to_dict(frame: SyntheticFrame) -> dict:
    return asdict(frame)


def generate_synthetic_frame(camera_id: str = "cam-01", recipe_id: str = "recipe-default") -> SyntheticFrame:
    frame_id = str(uuid4())
    captured_at = datetime.now(timezone.utc).isoformat()
    exposure_ms = round(random.uniform(5.0, 14.0), 3)
    gain_db = round(random.uniform(0.0, 6.0), 3)
    image_uri = f"synthetic://frame/{frame_id}.png"
    return SyntheticFrame(
        frame_id=frame_id,
        camera_id=camera_id,
        recipe_id=recipe_id,
        captured_at=captured_at,
        image_uri=image_uri,
        exposure_ms=exposure_ms,
        gain_db=gain_db,
    )


def capture_frame(camera_id: str = "cam-01", recipe_id: str = "recipe-default") -> SyntheticFrame:
    """Prefer edge-acquisition HTTP service; fall back to in-process synthetic capture in non-prod."""
    edge_url = os.getenv("EDGE_ACQUISITION_URL", "").strip().rstrip("/")
    if edge_url:
        try:
            headers = {"Content-Type": "application/json", **service_auth_headers()}
            with httpx.Client(timeout=3.0) as client:
                response = client.post(
                    f"{edge_url}/capture",
                    json={"camera_id": camera_id, "recipe_id": recipe_id},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return SyntheticFrame(
                    frame_id=data["frame_id"],
                    camera_id=data.get("camera_id", camera_id),
                    recipe_id=data.get("recipe_id", recipe_id),
                    captured_at=data.get("captured_at", datetime.now(timezone.utc).isoformat()),
                    image_uri=data.get("image_uri", f"synthetic://frame/{data['frame_id']}.png"),
                    exposure_ms=float(data.get("exposure_ms", 10.0)),
                    gain_db=float(data.get("gain_db", 0.0)),
                    image_b64=data.get("image_b64"),
                    image_width=data.get("image_width"),
                    image_height=data.get("image_height"),
                    capture_driver=data.get("capture_driver"),
                )
        except Exception as exc:
            if is_production():
                logger.exception("Edge capture failed in production — refusing synthetic fallback")
                raise RuntimeError(f"Edge capture failed: {exc}") from exc
            logger.warning("Edge capture failed; using synthetic frame: %s", exc)
    elif is_production():
        raise RuntimeError("EDGE_ACQUISITION_URL is required in production")
    return generate_synthetic_frame(camera_id=camera_id, recipe_id=recipe_id)
