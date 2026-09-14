"""EPC / process-id binding for EOL inspections."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

_SAFE = re.compile(r"[^A-Za-z0-9._:-]+")


def normalize_identifier(value: str | None, *, field: str = "id") -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) > 128:
        raise ValueError(f"{field} exceeds 128 characters")
    return text


def sanitize_path_component(value: str, *, fallback: str = "unknown") -> str:
    text = (value or "").strip() or fallback
    cleaned = _SAFE.sub("_", text)
    return cleaned.strip("._")[:96] or fallback


def bind_epc(
    *,
    epc: str | None = None,
    process_id: str | None = None,
    serial: str | None = None,
    lot_id: str | None = None,
    work_order: str | None = None,
    inspection_id: str | None = None,
    source: str = "api",
) -> dict:
    """Build a versioned EpcBinding document."""
    epc_norm = normalize_identifier(epc, field="epc")
    process_norm = normalize_identifier(process_id, field="process_id")
    serial_norm = normalize_identifier(serial, field="serial")
    lot_norm = normalize_identifier(lot_id, field="lot_id")
    wo_norm = normalize_identifier(work_order, field="work_order")
    unique = epc_norm or process_norm or serial_norm or f"anon-{inspection_id or uuid4()}"
    return {
        "schema": "EpcBinding",
        "schema_version": "1.0.0",
        "epc": epc_norm,
        "process_id": process_norm,
        "serial": serial_norm,
        "lot_id": lot_norm,
        "work_order": wo_norm,
        "unique_key": unique,
        "source": source,
        "bound_at": datetime.now(timezone.utc).isoformat(),
        "inspection_id": inspection_id,
    }


def extract_from_mapping(data: dict | None) -> dict:
    """Pull EPC-related keys from MQTT / OPC-UA / API payloads."""
    if not isinstance(data, dict):
        return {}
    aliases = {
        "epc": ("epc", "EPC", "Epc", "epc_id", "epcId", "tag", "rfid"),
        "process_id": ("process_id", "processId", "processID", "proc_id", "trace_id", "traceId"),
        "serial": ("serial", "serial_number", "serialNumber", "sn"),
        "lot_id": ("lot_id", "lotId", "lot"),
        "work_order": ("work_order", "workOrder", "wo", "order_id"),
        "recipe_id": ("recipe_id", "recipeId", "recipe"),
        "station_id": ("station_id", "stationId", "station"),
        "camera_id": ("camera_id", "cameraId"),
        "camera_ids": ("camera_ids", "cameraIds"),
    }
    out: dict = {}
    for target, keys in aliases.items():
        for key in keys:
            if key in data and data[key] not in (None, ""):
                out[target] = data[key]
                break
    return out
