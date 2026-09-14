from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .camera_limits import CERTIFIED_MAX_CAMERAS, HARD_CAP, max_cameras


def _clean_camera_ids(value: list[str] | None, *, allow_empty: bool = False) -> list[str] | None:
    if value is None:
        return None
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        cid = str(item).strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        cleaned.append(cid)
    if not cleaned:
        if allow_empty:
            return []
        raise ValueError("camera_ids must contain at least 1 camera")
    cap = max_cameras()
    if len(cleaned) > cap:
        raise ValueError(
            f"camera_ids allows at most {cap} cameras "
            f"(certified 1–{CERTIFIED_MAX_CAMERAS}, hard cap {HARD_CAP})"
        )
    return cleaned


class CaptureRequest(BaseModel):
    camera_id: str = Field(default="cam-01")
    recipe_id: str = Field(default="recipe-default")
    source: str | None = None
    epc: str | None = None
    process_id: str | None = None


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
        description="Optional cameras for same-case multi-view inspection",
    )
    epc: str | None = Field(default=None, description="Electronic Product Code / unique part id")
    process_id: str | None = Field(default=None, description="Related process / trace id")
    serial: str | None = None
    lot_id: str | None = None
    work_order: str | None = None
    station_id: str | None = None
    trigger_source: str | None = Field(default=None, description="api | mqtt | opcua | hmi")
    capture_only: bool = Field(default=False, description="Store images without inference")
    legal_hold: bool = False

    @field_validator("camera_ids")
    @classmethod
    def _validate_camera_ids(cls, value: list[str] | None) -> list[str] | None:
        return _clean_camera_ids(value)


class CameraSelectionRequest(BaseModel):
    camera_ids: list[str] = Field(..., min_length=1)

    @field_validator("camera_ids")
    @classmethod
    def _unique(cls, value: list[str]) -> list[str]:
        cleaned = _clean_camera_ids(value)
        assert cleaned is not None
        return cleaned


class RecipeThresholdsRequest(BaseModel):
    amber: float = Field(..., ge=0.0, le=1.0)
    red: float = Field(..., ge=0.0, le=1.0)


class RecipeCreateRequest(BaseModel):
    recipe_id: str = Field(..., min_length=2, max_length=63)
    name: str = Field(..., min_length=1, max_length=128)
    recipe_version: str = Field(default="v1", max_length=32)
    active: bool = False
    camera_profile: dict | None = None
    lighting_profile: dict | None = None
    decision_thresholds: RecipeThresholdsRequest | None = None

    @field_validator("recipe_id")
    @classmethod
    def _recipe_id(cls, value: str) -> str:
        from .core_store import validate_recipe_id

        return validate_recipe_id(value)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned


class RecipeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    recipe_version: str | None = Field(default=None, max_length=32)
    active: bool | None = None
    camera_profile: dict | None = None
    lighting_profile: dict | None = None
    decision_thresholds: RecipeThresholdsRequest | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned:
            raise ValueError("name cannot be empty")
        return cleaned


class RecipeDeleteRequest(BaseModel):
    confirm: bool = False
    confirm_recipe_id: str = ""


class MqttTriggerRequest(BaseModel):
    payload: dict | str | None = None
    topic: str | None = None


class RetentionPolicyRequest(BaseModel):
    ttl_days: int | None = Field(default=None, ge=1, le=3650)
    archive_bucket: str | None = None
    archive_prefix: str | None = None
    legal_hold_default: bool | None = None
    delete_after_archive: bool | None = None
    enabled: bool | None = None


class StationCloneRequest(BaseModel):
    station_id: str = Field(..., min_length=1, max_length=64)
    name: str | None = None
