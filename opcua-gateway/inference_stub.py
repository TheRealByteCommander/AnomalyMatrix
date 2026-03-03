from __future__ import annotations

import hashlib

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='AnomalyMatrix AI Inference Stub', version='0.1.0')


class InferenceRequest(BaseModel):
    frame_id: str
    camera_id: str
    recipe_id: str


@app.post('/infer')
def infer(payload: InferenceRequest):
    digest = hashlib.sha256(f"{payload.frame_id}-{payload.camera_id}-{payload.recipe_id}".encode()).hexdigest()
    score = round(int(digest[:8], 16) / 0xFFFFFFFF, 4)
    return {
        'anomaly_score': score,
        'status': 'anomaly' if score >= 0.7 else 'normal',
        'heatmap_uri': f'synthetic://heatmap/{payload.frame_id}.png',
        'model_version': 'patchcore-mvp-v0',
    }
