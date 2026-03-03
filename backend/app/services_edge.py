from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random
from uuid import uuid4


@dataclass
class SyntheticFrame:
    frame_id: str
    camera_id: str
    recipe_id: str
    captured_at: str
    image_uri: str
    exposure_ms: float
    gain_db: float


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
