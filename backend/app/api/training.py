from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request

from ..contracts.envelope import success_envelope
from ..core_store import CoreStore
from ..patchcore_memory import inspect_memory_bank
from ..rbac import require_permission, resolve_auth
from ..nio_store import count_nio_images
from ..training_service import (
    artifact_path_for_model,
    capture_good_part_samples,
    count_training_images,
    set_active_memory_bank,
    train_patchcore,
    validate_candidate,
)

router = APIRouter(tags=["training"])


def _store(request: Request) -> CoreStore:
    return request.app.state.core_store


def _events(request: Request):
    from .. import main as main_module

    return main_module.event_bus


def _cameras(request: Request):
    from .. import main as main_module

    return main_module.camera_station


def _data_root(request: Request) -> Path:
    return Path(request.app.state.core_store.data_root)


def _point_active_bank(request: Request, model: dict | None) -> str | None:
    data_root = _data_root(request)
    artifact = artifact_path_for_model(model)
    if artifact is None:
        uri = (model or {}).get("metadata", {}).get("artifact_uri") if model else None
        if uri:
            raise HTTPException(status_code=409, detail=f"Memory-bank artifact missing: {uri}")
        return set_active_memory_bank(data_root, None)
    return set_active_memory_bank(data_root, artifact)


def _resolve_capture_camera(request: Request, payload: dict) -> tuple[str, str | None]:
    selection = _cameras(request).load()
    sources = dict(selection.get("sources") or {})
    requested = str(payload.get("camera_id") or "").strip()
    if requested:
        return requested, sources.get(requested)
    selected = list(selection.get("camera_ids") or [])
    if selected:
        camera_id = str(selected[0])
        return camera_id, sources.get(camera_id)
    return "cam-01", sources.get("cam-01")


@router.post("/models/training-samples")
async def capture_training_samples(request: Request, payload: dict = Body(default_factory=dict)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.train")
    recipe_id = str(payload.get("recipe_id", "recipe-default")).strip() or "recipe-default"
    count = max(1, min(int(payload.get("count", 8)), 32))
    camera_id, source = _resolve_capture_camera(request, payload)
    try:
        captured = capture_good_part_samples(
            data_root=_data_root(request),
            recipe_id=recipe_id,
            camera_id=camera_id,
            count=count,
            source=source,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _store(request).append_audit(
        actor=auth.user_id,
        action="models.capture",
        resource_type="training_sample",
        resource_id=recipe_id,
        after_state={"saved": captured.get("saved"), "camera_id": camera_id, "count": captured.get("count")},
        request_id=request.state.request_id,
    )
    return success_envelope(captured, request.state.request_id)


@router.post("/models/train")
async def train_model(request: Request, payload: dict = Body(default_factory=dict)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.train")
    recipe_id = str(payload.get("recipe_id", "recipe-default")).strip()
    dataset_version = str(payload.get("dataset_version", "v1")).strip()
    sample_count = int(payload.get("sample_count", 12))

    trained = train_patchcore(
        data_root=_data_root(request),
        recipe_id=recipe_id,
        dataset_version=dataset_version,
        sample_count=max(3, min(sample_count, 64)),
    )
    registered = _store(request).register_model(trained)
    _store(request).append_audit(
        actor=auth.user_id,
        action="models.train",
        resource_type="model",
        resource_id=registered["model_id"],
        after_state=registered,
        request_id=request.state.request_id,
    )
    return success_envelope(registered, request.state.request_id)


@router.post("/models/{model_id}/promote")
async def promote_model(request: Request, model_id: str, payload: dict = Body(default_factory=dict)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.promote")
    model = _store(request).get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    meta = model.get("metadata") or {}
    sample_count = int(meta.get("sample_count") or 0)
    if sample_count <= 0:
        sample_count = int(meta.get("embedding_count") or 0)
    validation = validate_candidate(
        baseline_score=float(payload.get("baseline_score", 0.35)),
        candidate_score=float(payload.get("candidate_score", 0.30)),
        data_source=str(meta.get("data_source", "unknown")),
        sample_count=sample_count,
    )
    if not validation["passed"]:
        raise HTTPException(
            status_code=409,
            detail=f"Promotion validation failed: {validation['reason']}",
        )
    if meta.get("artifact_uri") and artifact_path_for_model(model) is None:
        raise HTTPException(status_code=409, detail=f"Memory-bank artifact missing: {meta.get('artifact_uri')}")

    before = _store(request).get_active_model()
    promoted = _store(request).promote_model(model_id)
    _point_active_bank(request, promoted)
    _store(request).append_audit(
        actor=auth.user_id,
        action="models.promote",
        resource_type="model",
        resource_id=model_id,
        before_state=before,
        after_state=promoted,
        request_id=request.state.request_id,
    )
    event = _events(request).emit(
        "ModelRetrained",
        {
            "model_id": model_id,
            "model_version": promoted.get("model_version"),
            "dataset_version": promoted.get("dataset_version"),
            "recipe_id": promoted.get("metadata", {}).get("recipe_id"),
            "validation": validation,
        },
    )
    promoted["domain_event_id"] = event.get("event_id")
    return success_envelope({"model": promoted, "validation": validation}, request.state.request_id)


@router.post("/models/{model_id}/activate")
async def activate_model(request: Request, model_id: str):
    """Reuse a stored memory bank without retraining (candidate, archived, or rolled_back)."""
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.promote")
    model = _store(request).get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    meta = model.get("metadata") or {}
    if meta.get("artifact_uri") and artifact_path_for_model(model) is None:
        raise HTTPException(status_code=409, detail=f"Memory-bank artifact missing: {meta.get('artifact_uri')}")

    before = _store(request).get_active_model()
    activated = _store(request).promote_model(model_id)
    _point_active_bank(request, activated)
    _store(request).append_audit(
        actor=auth.user_id,
        action="models.activate",
        resource_type="model",
        resource_id=model_id,
        before_state=before,
        after_state=activated,
        request_id=request.state.request_id,
    )
    return success_envelope(
        {
            "model": activated,
            "previous": before,
            "memory_bank": inspect_memory_bank(_data_root(request)),
        },
        request.state.request_id,
    )


@router.post("/models/rollback")
async def rollback_model(request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.rollback")
    before = _store(request).get_active_model()
    restored = _store(request).rollback_model()
    if not restored:
        raise HTTPException(status_code=404, detail="No archived model available for rollback")
    try:
        _point_active_bank(request, restored)
    except HTTPException:
        set_active_memory_bank(_data_root(request), None)
    _store(request).append_audit(
        actor=auth.user_id,
        action="models.rollback",
        resource_type="model",
        resource_id=restored.get("model_id"),
        before_state=before,
        after_state=restored,
        request_id=request.state.request_id,
    )
    return success_envelope({"restored_model": restored, "rolled_back": before}, request.state.request_id)


def models_catalog_payload(store: CoreStore, *, recipe_id: str = "recipe-default") -> dict:
    items = store.list_models()
    active = next((m for m in items if m.get("status") == "active"), items[0] if items else None)
    return {
        "items": items,
        "count": len(items),
        "active": active,
        "memory_bank": inspect_memory_bank(store.data_root),
        "training_samples": {
            "recipe_id": recipe_id,
            "count": count_training_images(store.data_root, recipe_id),
        },
        "nio_samples": {
            "recipe_id": recipe_id,
            "count": count_nio_images(store.data_root, recipe_id),
        },
    }
