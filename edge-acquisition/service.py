from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='AnomalyMatrix Edge Acquisition Stub', version='0.1.0')


class CaptureRequest(BaseModel):
    camera_id: str = 'cam-01'
    recipe_id: str = 'recipe-default'


@app.post('/capture')
def capture(payload: CaptureRequest):
    frame_id = str(uuid4())
    return {
        'frame_id': frame_id,
        'camera_id': payload.camera_id,
        'recipe_id': payload.recipe_id,
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'image_uri': f'synthetic://frame/{frame_id}.png',
    }
