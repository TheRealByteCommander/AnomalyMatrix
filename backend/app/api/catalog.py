from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request

from ..contracts.envelope import success_envelope
from ..core_store import CoreStore, RecipeError
from ..event_bus import DomainEventBus
from ..models import RecipeCreateRequest, RecipeDeleteRequest, RecipeThresholdsRequest, RecipeUpdateRequest
from ..nio_store import count_nio_images
from ..qa_feedback import apply_qa_verdict
from ..rbac import require_permission, resolve_auth
from .training import models_catalog_payload

router = APIRouter(tags=["catalog"])


def _store(request: Request) -> CoreStore:
    return request.app.state.core_store


def _events(_request: Request) -> DomainEventBus:
    from .. import main as main_module

    return main_module.event_bus


def _repo(request: Request):
    repo = getattr(request.app.state, "repo", None)
    if repo is not None:
        return repo
    from .. import main as main_module

    return main_module.repo


def _http_from_recipe(exc: Exception) -> HTTPException:
    if isinstance(exc, RecipeError):
        return HTTPException(status_code=exc.status_code, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    raise exc


@router.get("/recipes")
async def list_recipes(request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.read")
    items = _store(request).list_recipes()
    return success_envelope({"items": items, "count": len(items)}, request.state.request_id)


@router.post("/recipes")
async def create_recipe(request: Request, payload: RecipeCreateRequest):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.write")
    thresholds = payload.decision_thresholds
    try:
        recipe = _store(request).create_recipe(
            recipe_id=payload.recipe_id,
            name=payload.name,
            recipe_version=payload.recipe_version,
            active=payload.active,
            camera_profile=payload.camera_profile,
            lighting_profile=payload.lighting_profile,
            amber=thresholds.amber if thresholds else None,
            red=thresholds.red if thresholds else None,
        )
    except Exception as exc:
        raise _http_from_recipe(exc) from exc
    _store(request).append_audit(
        actor=auth.user_id,
        action="recipes.create",
        resource_type="recipe",
        resource_id=recipe["recipe_id"],
        after_state=recipe,
        request_id=request.state.request_id,
    )
    return success_envelope(recipe, request.state.request_id)


@router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.read")
    recipe = _store(request).get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe not found: {recipe_id}")
    return success_envelope(recipe, request.state.request_id)


@router.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, request: Request, payload: RecipeUpdateRequest):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.write")
    thresholds = payload.decision_thresholds
    try:
        before = _store(request).get_recipe(recipe_id)
        recipe = _store(request).update_recipe(
            recipe_id,
            name=payload.name,
            recipe_version=payload.recipe_version,
            active=payload.active,
            camera_profile=payload.camera_profile,
            lighting_profile=payload.lighting_profile,
            amber=thresholds.amber if thresholds else None,
            red=thresholds.red if thresholds else None,
        )
    except Exception as exc:
        raise _http_from_recipe(exc) from exc
    _store(request).append_audit(
        actor=auth.user_id,
        action="recipes.update",
        resource_type="recipe",
        resource_id=recipe_id,
        before_state=before,
        after_state=recipe,
        request_id=request.state.request_id,
    )
    return success_envelope(recipe, request.state.request_id)


@router.delete("/recipes/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    request: Request,
    payload: RecipeDeleteRequest = Body(default=RecipeDeleteRequest()),
):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.write")
    try:
        result = _store(request).delete_recipe(
            recipe_id,
            confirm=payload.confirm,
            confirm_recipe_id=payload.confirm_recipe_id,
        )
    except Exception as exc:
        raise _http_from_recipe(exc) from exc
    _store(request).append_audit(
        actor=auth.user_id,
        action="recipes.delete",
        resource_type="recipe",
        resource_id=recipe_id,
        before_state=result.get("recipe"),
        after_state={
            "deleted": True,
            "archived_assets": result.get("archived_assets"),
            "activated_fallback": result.get("activated_fallback"),
        },
        request_id=request.state.request_id,
    )
    return success_envelope(result, request.state.request_id)


@router.put("/recipes/{recipe_id}/thresholds")
async def update_recipe_thresholds(recipe_id: str, request: Request, payload: RecipeThresholdsRequest):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.write")
    try:
        recipe = _store(request).update_recipe_thresholds(recipe_id, amber=payload.amber, red=payload.red)
    except Exception as exc:
        raise _http_from_recipe(exc) from exc
    _store(request).append_audit(
        actor=auth.user_id,
        action="recipes.thresholds",
        resource_type="recipe",
        resource_id=recipe_id,
        after_state=recipe,
        request_id=request.state.request_id,
    )
    return success_envelope(recipe, request.state.request_id)


@router.get("/models")
async def list_models(request: Request, recipe_id: str | None = Query(default=None)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.read")
    recipe = str(recipe_id or "recipe-default").strip() or "recipe-default"
    payload = models_catalog_payload(_store(request), recipe_id=recipe)
    return success_envelope(payload, request.state.request_id)


@router.get("/audit/recent")
async def audit_recent(request: Request, limit: int = Query(default=50, ge=1, le=200)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "audit.read")
    # Audit read from postgres only for now; JSONL via core_store append only
    store = _store(request)
    if store.use_postgres:
        with store._connect() as conn:
            from psycopg2.extras import RealDictCursor

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,))
                items = [dict(r) for r in cur.fetchall()]
    else:
        items = []
        if store._audit_file.exists():
            for line in store._audit_file.read_text(encoding="utf-8").splitlines()[-limit:]:
                import json

                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        items = list(reversed(items))
    return success_envelope({"items": items, "count": len(items)}, request.state.request_id)


@router.post("/feedback")
async def submit_feedback(request: Request, payload: dict = Body(...)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "feedback.submit")
    inspection_id = str(payload.get("inspection_id", "")).strip()
    verdict = str(payload.get("verdict", "")).strip()
    comment = str(payload.get("comment", "")).strip()
    if not inspection_id or verdict not in {"confirm_anomaly", "false_positive", "needs_review"}:
        raise HTTPException(status_code=400, detail="inspection_id and valid verdict required")

    store = _store(request)
    entry = store.append_feedback(
        inspection_id=inspection_id,
        actor=auth.user_id,
        verdict=verdict,
        comment=comment,
        recipe_version=str(payload.get("recipe_version", "v1")),
        model_version=str(payload.get("model_version", "v0")),
    )
    applied = apply_qa_verdict(
        repo=_repo(request),
        data_root=store.data_root,
        inspection_id=inspection_id,
        verdict=verdict,
        actor=auth.user_id,
        feedback_id=entry["feedback_id"],
        comment=comment,
    )
    entry["inspection"] = applied.get("inspection")
    entry["nio_sample"] = applied.get("nio_sample")
    entry["decision_override"] = applied.get("decision_override")
    if applied.get("inspection"):
        entry["decision"] = applied["inspection"].get("decision")
        recipe_id = str((applied["inspection"].get("frame") or {}).get("recipe_id") or "recipe-default")
        entry["nio_count"] = count_nio_images(store.data_root, recipe_id)
    store.append_audit(
        actor=auth.user_id,
        action="feedback.submit",
        resource_type="inspection",
        resource_id=inspection_id,
        after_state={
            "feedback_id": entry["feedback_id"],
            "verdict": verdict,
            "decision": (applied.get("inspection") or {}).get("decision"),
            "decision_override": applied.get("decision_override"),
            "qa": (applied.get("inspection") or {}).get("qa"),
            "nio_sample": (applied.get("nio_sample") or {}).get("path"),
        },
        request_id=request.state.request_id,
    )
    event = _events(request).emit(
        "FeedbackSubmitted",
        {
            "feedback_id": entry["feedback_id"],
            "inspection_id": inspection_id,
            "actor": auth.user_id,
            "verdict": verdict,
            "comment": comment,
        },
    )
    entry["domain_event_id"] = event.get("event_id")
    return success_envelope(entry, request.state.request_id)


@router.get("/feedback")
async def list_feedback(request: Request, inspection_id: str | None = None, limit: int = Query(default=50, ge=1, le=200)):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "feedback.read")
    items = _store(request).list_feedback(inspection_id=inspection_id, limit=limit)
    return success_envelope({"items": items, "count": len(items)}, request.state.request_id)
