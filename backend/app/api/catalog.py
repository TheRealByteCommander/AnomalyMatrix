from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request

from ..contracts.envelope import success_envelope
from ..core_store import CoreStore
from ..event_bus import DomainEventBus
from ..rbac import require_permission, resolve_auth

router = APIRouter(tags=["catalog"])


def _store(request: Request) -> CoreStore:
    return request.app.state.core_store


def _events(_request: Request) -> DomainEventBus:
    from .. import main as main_module

    return main_module.event_bus


@router.get("/recipes")
async def list_recipes(request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "recipes.read")
    items = _store(request).list_recipes()
    return success_envelope({"items": items, "count": len(items)}, request.state.request_id)


@router.get("/models")
async def list_models(request: Request):
    auth = resolve_auth(request, _store(request))
    require_permission(auth, "models.read")
    items = _store(request).list_models()
    return success_envelope({"items": items, "count": len(items)}, request.state.request_id)


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
    store.append_audit(
        actor=auth.user_id,
        action="feedback.submit",
        resource_type="inspection",
        resource_id=inspection_id,
        after_state=entry,
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
