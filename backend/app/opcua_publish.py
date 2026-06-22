from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


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


def map_inspection_to_opcua_payload(result: dict) -> dict:
    inference = result.get("inference", {})
    return {
        "ns=2;s=Inspection.LastResult.PassFail": inference.get("status", "unknown"),
        "ns=2;s=Inspection.LastResult.AnomalyScore": inference.get("anomaly_score", 0.0),
        "ns=2;s=Inspection.LastResult.DefectClass": _defect_class(result),
        "ns=2;s=Inspection.LastResult.HeatmapUri": inference.get("heatmap_uri", ""),
        "ns=2;s=Inspection.LastResult.ModelVersion": inference.get("model_version", ""),
        "ns=2;s=Inspection.LastResult.InspectionId": result.get("inspection_id", ""),
        "ns=2;s=Inspection.LastResult.Timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish_to_opcua(result: dict, endpoint: str | None = None) -> OpcUaPublishResult:
    payload = map_inspection_to_opcua_payload(result)
    endpoint = endpoint or os.getenv("OPCUA_ENDPOINT", "opc.tcp://localhost:4840")
    gateway = os.getenv("OPCUA_GATEWAY_URL", "").strip().rstrip("/")

    if gateway:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.post(
                    f"{gateway}/publish",
                    json={"endpoint": endpoint, "payload": payload},
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

    # Skeleton transport when no gateway URL configured (documented Phase 3 behavior).
    return OpcUaPublishResult(published=True, endpoint=endpoint, payload=payload)
