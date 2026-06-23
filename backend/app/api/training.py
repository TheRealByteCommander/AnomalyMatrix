from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request

from ..contracts.envelope import success_envelope
from ..core_store import CoreStore
from ..rbac import require_permission, resolve_auth
from ..training_service import train_patchcore, validate_candidate

router = APIRouter(tags=["training"])


def _store(request: Request) -> CoreStore:
    return request.app.state.core_store


def _events(request: Request):
    from .. import main as main_module

    return main_module.event_bus


def _data_root(request: Request) -> Path:
    return Path(request.app.state.core_store.data_root)


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
    validation = validate_candidate(
        baseline_score=float(payload.get("baseline_score", 0.35)),
        candidate_score=float(payload.get("candidate_score", 0.30)),
        data_source=str(meta.get("data_source", "unknown")),
        sample_count=int(meta.get("embedding_count", 0)),
    )
    if not validation["passed"]:
        raise HTTPException(status_code=409, detail=validation)

    before = _store(request).get_active_model()
    promoted = _store(request).promote_model(model_id)
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


@router.post("/models/rollback")
async def rollback_model(request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.rollback")
    before = _store(request).get_active_model()
    restored = _store(request).rollback_model()
    if not restored:
        raise HTTPException(status_code=404, detail="No archived model available for rollback")
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
