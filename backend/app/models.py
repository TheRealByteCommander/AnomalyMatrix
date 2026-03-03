from __future__ import annotations

from pydantic import BaseModel, Field


class CaptureRequest(BaseModel):
    camera_id: str = Field(default='cam-01')
    recipe_id: str = Field(default='recipe-default')


class InferRequest(BaseModel):
    frame_id: str
    camera_id: str
    recipe_id: str


class RunInspectionRequest(BaseModel):
    camera_id: str = Field(default='cam-01')
    recipe_id: str = Field(default='recipe-default')
