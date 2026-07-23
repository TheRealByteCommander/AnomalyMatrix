from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .opcua_nodes import load_opcua_contract, node
from .service_auth import service_auth_headers


@dataclass
class OpcUaPublishResult:
    published: bool
    endpoint: str
    payload: dict


def _defect_class(result: dict) -> str:
    decision = result.get("decision", "green")
    if decision == "red":
        return str(result.get("inference", {}).get("defect_class") or "critical")
    if decision == "amber":
        return "review"
    return "none"


def _decision_code(decision: str) -> int:
    codes = load_opcua_contract().get("decision_codes", {})
    return int(codes.get(decision, 0))


def _stop_on_red_enabled() -> bool:
    return os.getenv("OPCUA_PLC_STOP_ON_RED", "true").strip().lower() in {"1", "true", "yes"}


def map_inspection_to_opcua_payload(result: dict, *, busy: bool = False) -> dict:
    """Map inspection result to OPC UA node values including PLC stop/reject signals."""
    inference = result.get("inference", {})
    decision = result.get("decision", "green")
    is_red = decision == "red"
    stop_on_red = _stop_on_red_enabled()

    payload = {
        node("last_result.pass_fail"): inference.get("status", "unknown"),
        node("last_result.pass_fail_bool"): decision == "green",
        node("last_result.anomaly_score"): float(inference.get("anomaly_score", 0.0)),
        node("last_result.defect_class"): _defect_class(result),
        node("last_result.heatmap_uri"): inference.get("heatmap_uri", ""),
        node("last_result.model_version"): inference.get("model_version", ""),
        node("last_result.inspection_id"): result.get("inspection_id", ""),
        node("last_result.timestamp"): datetime.now(timezone.utc).isoformat(),
        node("last_result.decision_code"): _decision_code(decision),
        node("inspection.busy"): busy,
        node("inspection.result_ready"): not busy,
        node("inspection.stop_line_request"): is_red and stop_on_red,
        node("inspection.reject_part"): is_red,
        node("system_state"): "busy" if busy else "ready",
    }

    frame = result.get("frame") or {}
    if frame.get("recipe_id"):
        payload[node("active_recipe")] = str(frame["recipe_id"])

    trend = result.get("trend_warning")
    if trend is not None:
        payload[node("trend_warning")] = bool(trend)

    return payload


def map_inspection_busy_payload(*, camera_id: str = "", recipe_id: str = "") -> dict:
    payload = {
        node("inspection.busy"): True,
        node("inspection.result_ready"): False,
        node("system_state"): "busy",
        node("inspection.stop_line_request"): False,
        node("inspection.reject_part"): False,
    }
    if camera_id:
        payload[node("inspection.camera_id")] = camera_id
    if recipe_id:
        payload[node("inspection.recipe_id")] = recipe_id
    return payload


def publish_opcua_payload(payload: dict, endpoint: str | None = None) -> OpcUaPublishResult:
    endpoint = endpoint or os.getenv("OPCUA_ENDPOINT", "opc.tcp://localhost:4840")
    gateway = os.getenv("OPCUA_GATEWAY_URL", "").strip().rstrip("/")

    if gateway:
        try:
            headers = {"Content-Type": "application/json", **service_auth_headers()}
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{gateway}/publish",
                    json={"endpoint": endpoint, "payload": payload},
                    headers=headers,
                )
                response.raise_for_status()
                body = response.json()
                return OpcUaPublishResult(
                    published=bool(body.get("published", True)),
                    endpoint=body.get("endpoint", endpoint),
                    payload=payload,
                )
        except Exception:
            return OpcUaPublishResult(published=False, endpoint=endpoint, payload=payload)

    return OpcUaPublishResult(published=True, endpoint=endpoint, payload=payload)


def publish_to_opcua(result: dict, endpoint: str | None = None) -> OpcUaPublishResult:
    payload = map_inspection_to_opcua_payload(result, busy=False)
    return publish_opcua_payload(payload, endpoint=endpoint)


def publish_busy_state(camera_id: str = "", recipe_id: str = "") -> OpcUaPublishResult:
    payload = map_inspection_busy_payload(camera_id=camera_id, recipe_id=recipe_id)
    return publish_opcua_payload(payload)
