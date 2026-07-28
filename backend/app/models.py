from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CaptureRequest(BaseModel):
    camera_id: str = Field(default="cam-01")
    recipe_id: str = Field(default="recipe-default")
    source: str | None = None


class InferRequest(BaseModel):
    frame_id: str
    camera_id: str
    recipe_id: str


class RunInspectionRequest(BaseModel):
    camera_id: str | None = Field(
        default=None,
        description="Single-camera override (legacy). Ignored when camera_ids is set.",
    )
    recipe_id: str = Field(default="recipe-default")
    camera_ids: list[str] | None = Field(
        default=None,
        description="Optional 1–4 cameras for same-case multi-view inspection",
    )

    @field_validator("camera_ids")
    @classmethod
    def _validate_camera_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = []
        seen = set()
        for item in value:
            cid = str(item).strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            cleaned.append(cid)
        if len(cleaned) < 1:
            raise ValueError("camera_ids must contain at least 1 camera")
        if len(cleaned) > 4:
            raise ValueError("camera_ids allows at most 4 cameras")
        return cleaned


class CameraSelectionRequest(BaseModel):
    camera_ids: list[str] = Field(..., min_length=1, max_length=4)

    @field_validator("camera_ids")
    @classmethod
    def _unique(cls, value: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for item in value:
            cid = str(item).strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            cleaned.append(cid)
        if not cleaned:
            raise ValueError("At least one camera_id required")
        if len(cleaned) > 4:
            raise ValueError("At most 4 cameras allowed")
        return cleaned
