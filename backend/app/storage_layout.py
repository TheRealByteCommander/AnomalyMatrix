"""Structured object-key convention and capture metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .epc import sanitize_path_component

SCHEMA_VERSION = "1.0.0"


def station_id() -> str:
    return os.getenv("AMX_STATION_ID", "eol-station-01").strip() or "eol-station-01"


def object_key(
    *,
    station: str,
    recipe_id: str,
    epc: str,
    camera_id: str,
    captured_at: datetime | None = None,
    decision: str = "pending",
    ext: str = "png",
    kind: str = "image",
) -> str:
    ts = captured_at or datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%dT%H%M%S%fZ")
    parts = [
        sanitize_path_component(station, fallback="station"),
        sanitize_path_component(recipe_id, fallback="recipe-default"),
        sanitize_path_component(epc, fallback="unbound"),
        ts.strftime("%Y"),
        ts.strftime("%m"),
        ts.strftime("%d"),
        f"{stamp}_{sanitize_path_component(camera_id, fallback='cam')}_{sanitize_path_component(decision)}_{kind}.{ext.lstrip('.')}",
    ]
    return "/".join(parts)


def image_asset(
    *,
    inspection_id: str,
    camera_id: str,
    recipe_id: str,
    epc: str | None,
    captured_at: str,
    object_name: str,
    bytes_len: int,
    content_type: str,
    width: int | None = None,
    height: int | None = None,
    colorspace: str | None = None,
    format_name: str = "png",
    decision: str | None = None,
    legal_hold: bool = False,
    extra: dict | None = None,
) -> dict:
    asset = {
        "schema": "ImageAsset",
        "schema_version": SCHEMA_VERSION,
        "asset_id": str(uuid4()),
        "inspection_id": inspection_id,
        "station_id": station_id(),
        "recipe_id": recipe_id,
        "epc": epc,
        "camera_id": camera_id,
        "captured_at": captured_at,
        "object_key": object_name,
        "bytes": bytes_len,
        "content_type": content_type,
        "width": width,
        "height": height,
        "colorspace": colorspace,
        "format": format_name,
        "decision": decision,
        "legal_hold": legal_hold,
    }
    if extra:
        asset.update(extra)
    return asset


def capture_set(
    *,
    inspection_id: str,
    recipe_id: str,
    epc_binding: dict,
    assets: list[dict],
    decision: str,
    trigger_source: str,
) -> dict:
    return {
        "schema": "CaptureSet",
        "schema_version": SCHEMA_VERSION,
        "capture_set_id": inspection_id,
        "station_id": station_id(),
        "recipe_id": recipe_id,
        "epc_binding": epc_binding,
        "asset_count": len(assets),
        "assets": assets,
        "decision": decision,
        "trigger_source": trigger_source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def write_sidecar(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
