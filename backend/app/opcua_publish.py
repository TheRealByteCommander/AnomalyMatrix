from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OpcUaPublishResult:
    published: bool
    endpoint: str
    payload: dict


def map_inspection_to_opcua_payload(result: dict) -> dict:
    return {
        "ns=2;s=Inspection.LastResult.PassFail": result.get("inference", {}).get("status", "unknown"),
        "ns=2;s=Inspection.LastResult.AnomalyScore": result.get("inference", {}).get("anomaly_score", 0.0),
        "ns=2;s=Inspection.LastResult.HeatmapUri": result.get("inference", {}).get("heatmap_uri", ""),
        "ns=2;s=Inspection.LastResult.ModelVersion": result.get("inference", {}).get("model_version", ""),
        "ns=2;s=Inspection.LastResult.InspectionId": result.get("inspection_id", ""),
        "ns=2;s=Inspection.LastResult.Timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish_to_opcua(result: dict, endpoint: str = "opc.tcp://localhost:4840") -> OpcUaPublishResult:
    payload = map_inspection_to_opcua_payload(result)
    # MVP skeleton: payload mapping is concrete, transport publish is integration point.
    return OpcUaPublishResult(published=True, endpoint=endpoint, payload=payload)
