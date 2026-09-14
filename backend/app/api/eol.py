"""EOL station standard, MQTT trigger, storage, retention, watchdog APIs."""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from ..camera_limits import CERTIFIED_MAX_CAMERAS, HARD_CAP, max_cameras
from ..contracts.envelope import success_envelope
from ..models import MqttTriggerRequest, RetentionPolicyRequest, StationCloneRequest
from ..mqtt_trigger import ingest_message, mqtt_config, parse_mqtt_payload, status_snapshot
from ..rbac import require_permission, resolve_auth
from ..recommendations import build_recommendations
from ..retention import apply_local_retention, apply_minio_retention
from ..station_vision import CHECKLIST_ITEMS, StationVisionError
from ..storage_minio import storage_stats

router = APIRouter(tags=["eol-vision"])


def _auth(request: Request):
    store = request.app.state.core_store
    auth = resolve_auth(request, store)
    request.state.auth = auth
    return auth


@router.get("/station/vision-profile")
async def vision_profile_get(request: Request):
    _auth(request)
    require_permission(request.state.auth, "cameras.read")
    profile = request.app.state.vision_store.load()
    return success_envelope(
        {
            **profile,
            "roles": ["top", "side", "bottom", "stf", "completeness", "other"],
            "checklist_items": list(CHECKLIST_ITEMS),
            "max_cameras": max_cameras(),
            "certified_max_cameras": CERTIFIED_MAX_CAMERAS,
            "hard_cap": HARD_CAP,
        },
        request.state.request_id,
    )


@router.put("/station/vision-profile")
async def vision_profile_put(request: Request, payload: dict = Body(...)):
    auth = _auth(request)
    require_permission(auth, "cameras.configure")
    try:
        saved = request.app.state.vision_store.save(payload, actor=auth.user_id)
    except StationVisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    request.app.state.core_store.append_audit(
        actor=auth.user_id,
        action="station.vision_profile",
        resource_type="station_vision",
        resource_id=saved.get("station_id", "default"),
        after_state={"camera_count": len(saved.get("cameras") or [])},
        request_id=request.state.request_id,
    )
    return success_envelope(saved, request.state.request_id)


@router.get("/station/vision-profile/export")
async def vision_profile_export(request: Request, format: str = Query(default="json")):
    _auth(request)
    require_permission(request.state.auth, "cameras.read")
    text, media = request.app.state.vision_store.export_text(fmt=format)
    filename = f"eol-station-standard.{'yaml' if format.lower() in {'yaml', 'yml'} else 'json'}"
    return PlainTextResponse(
        text,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/station/vision-profile/import")
async def vision_profile_import(request: Request, payload: dict = Body(...)):
    auth = _auth(request)
    require_permission(auth, "cameras.configure")
    body = payload.get("content") or payload.get("template") or ""
    if not body and payload.get("schema") == "StationVisionProfile":
        import json

        body = json.dumps(payload)
    try:
        saved = request.app.state.vision_store.import_text(str(body), actor=auth.user_id)
    except (StationVisionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_envelope(saved, request.state.request_id)


@router.post("/station/vision-profile/clone")
async def vision_profile_clone(request: Request, payload: StationCloneRequest):
    auth = _auth(request)
    require_permission(auth, "cameras.configure")
    try:
        saved = request.app.state.vision_store.clone(
            new_station_id=payload.station_id,
            new_name=payload.name,
            actor=auth.user_id,
        )
    except StationVisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_envelope(saved, request.state.request_id)


@router.get("/station/recommendations")
async def station_recommendations(request: Request):
    _auth(request)
    require_permission(request.state.auth, "cameras.read")
    profile = request.app.state.vision_store.load()
    stats = storage_stats(data_root=request.app.state.core_store.data_root)
    return success_envelope(build_recommendations(profile=profile, stats=stats), request.state.request_id)


@router.get("/storage/stats")
async def storage_stats_get(request: Request):
    _auth(request)
    require_permission(request.state.auth, "trends.read")
    stats = storage_stats(data_root=request.app.state.core_store.data_root)
    return success_envelope(stats, request.state.request_id)


@router.get("/storage/retention")
async def retention_get(request: Request):
    _auth(request)
    require_permission(request.state.auth, "cameras.read")
    return success_envelope(request.app.state.retention_store.load(), request.state.request_id)


@router.put("/storage/retention")
async def retention_put(request: Request, payload: RetentionPolicyRequest):
    auth = _auth(request)
    require_permission(auth, "cameras.configure")
    try:
        saved = request.app.state.retention_store.save(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_envelope(saved, request.state.request_id)


@router.post("/storage/retention/run")
async def retention_run(request: Request):
    auth = _auth(request)
    require_permission(auth, "cameras.configure")
    policy = request.app.state.retention_store.load()
    local = apply_local_retention(root=request.app.state.core_store.data_root / "captures", policy=policy)
    remote = apply_minio_retention(policy)
    return success_envelope({"local": local, "minio": remote, "policy": policy}, request.state.request_id)


@router.get("/mqtt/status")
async def mqtt_status(request: Request):
    _auth(request)
    require_permission(request.state.auth, "inspection.read")
    return success_envelope({**status_snapshot(), "config": {k: v for k, v in mqtt_config().items() if k != "username"}}, request.state.request_id)


@router.post("/triggers/mqtt")
async def mqtt_trigger_simulate(request: Request, payload: MqttTriggerRequest):
    """Commissioning / tests: inject an MQTT-shaped payload without a broker."""
    auth = _auth(request)
    require_permission(auth, "inspection.run")
    body = payload.payload if payload.payload is not None else {}
    parsed = parse_mqtt_payload(body)
    try:
        result = ingest_message(body)
    except RuntimeError:
        from ..main import execute_inspection
        from ..models import RunInspectionRequest

        result = execute_inspection(
            RunInspectionRequest(
                recipe_id=str(parsed.get("recipe_id") or "recipe-default"),
                camera_id=parsed.get("camera_id"),
                camera_ids=parsed.get("camera_ids"),
                epc=parsed.get("epc"),
                process_id=parsed.get("process_id"),
                serial=parsed.get("serial"),
                lot_id=parsed.get("lot_id"),
                work_order=parsed.get("work_order"),
                trigger_source="mqtt",
                capture_only=parsed.get("action") == "capture",
            ),
            auth=auth,
            request_id=request.state.request_id,
        )
    return success_envelope({"parsed": parsed, "result": result}, request.state.request_id)


@router.get("/system/watchdog")
async def system_watchdog(request: Request):
    _auth(request)
    require_permission(request.state.auth, "inspection.read")
    snap = request.app.state.capture_watchdog.snapshot()
    from ..mqtt_trigger import status_snapshot as mqtt_snap

    return success_envelope(
        {
            **snap,
            "mqtt": mqtt_snap(),
            "opcua": {"enabled": True},
        },
        request.state.request_id,
    )


@router.post("/system/self-test")
async def system_self_test(request: Request):
    _auth(request)
    require_permission(request.state.auth, "inspection.read")
    from ..api.health import readiness_payload

    ready_payload, ready = readiness_payload()
    watchdog = request.app.state.capture_watchdog.snapshot()
    cameras = True
    try:
        from ..services_edge import list_edge_cameras

        discovered = list_edge_cameras()
        cameras = bool(discovered.get("cameras"))
    except Exception:
        cameras = False
    checks = {
        "ready": ready,
        "cameras_discovered": cameras,
        "watchdog": watchdog.get("status") in {"ok", "idle", "gap"},
        "vision_profile": bool(request.app.state.vision_store.load().get("station_id")),
        "mqtt_optional": (not mqtt_config()["enabled"]) or status_snapshot().get("connected"),
    }
    ok = bool(checks["ready"] and checks["vision_profile"])
    return success_envelope(
        {
            "ok": ok,
            "checks": checks,
            "readiness": ready_payload,
            "watchdog": watchdog,
        },
        request.state.request_id,
    )


@router.get("/contracts/eol")
async def contracts_eol(request: Request):
    _auth(request)
    require_permission(request.state.auth, "contracts.read")
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "contracts"
    names = {
        "ImageAsset": "image_asset_v1.json",
        "CaptureSet": "capture_set_v1.json",
        "EpcBinding": "epc_binding_v1.json",
        "StationVisionProfile": "station_vision_profile_v1.json",
        "RetentionPolicy": "retention_policy_v1.json",
    }
    schemas = {}
    for key, filename in names.items():
        path = root / filename
        schemas[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return success_envelope({"schema_version": "1.0.0", "schemas": schemas}, request.state.request_id)
