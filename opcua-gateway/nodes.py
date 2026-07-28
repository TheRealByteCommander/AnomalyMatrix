from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONTRACT = Path(__file__).resolve().parent  # resolved via candidates in load_contract


@lru_cache(maxsize=1)
def load_contract() -> dict:
    candidates = [
        Path(__file__).resolve().parents[1] / "contracts" / "opcua_nodeset_mapping_v1.json",
        Path(__file__).resolve().parent / "opcua_nodeset_mapping_v1.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("opcua_nodeset_mapping_v1.json not found")


def build_default_node_values() -> dict[str, object]:
    c = load_contract()
    insp = c.get("inspection", {})
    lr = c.get("last_result", {})
    trend = c.get("trend") or {}
    return {
        c["system_state"]: "ready",
        c.get("system_health", "ns=2;s=System.Health"): "ok",
        c["active_recipe"]: "recipe-default",
        insp["busy"]: False,
        insp["external_trigger"]: False,
        insp["start_request"]: False,
        insp["acknowledge_stop"]: False,
        insp["stop_line_request"]: False,
        insp["reject_part"]: False,
        insp["result_ready"]: False,
        # Empty CameraId => API uses station multi-camera selection
        insp.get("camera_id", "ns=2;s=Inspection.Request.CameraId"): "",
        insp.get("recipe_id", "ns=2;s=Inspection.Request.RecipeId"): "recipe-default",
        lr["pass_fail"]: "unknown",
        lr.get("pass_fail_bool", "ns=2;s=Inspection.LastResult.PassFailBool"): False,
        lr["anomaly_score"]: 0.0,
        lr["defect_class"]: "none",
        lr.get("decision_code", "ns=2;s=Inspection.LastResult.DecisionCode"): 0,
        lr.get("heatmap_uri", "ns=2;s=Inspection.LastResult.HeatmapUri"): "",
        lr.get("model_version", "ns=2;s=Inspection.LastResult.ModelVersion"): "",
        lr.get("inspection_id", "ns=2;s=Inspection.LastResult.InspectionId"): "",
        lr.get("timestamp", "ns=2;s=Inspection.LastResult.Timestamp"): "",
        lr.get("worst_view_camera_id", "ns=2;s=Inspection.LastResult.WorstViewCameraId"): "",
        lr.get("camera_ids", "ns=2;s=Inspection.LastResult.CameraIds"): "",
        lr.get("view_count", "ns=2;s=Inspection.LastResult.ViewCount"): 0,
        lr.get("decision_policy", "ns=2;s=Inspection.LastResult.DecisionPolicy"): "worst_view",
        c["trend_warning"]: False,
        trend.get("warning", c["trend_warning"]): False,
        trend.get("severity", "ns=2;s=Inspection.Trend.Severity"): "green",
        trend.get("reason", "ns=2;s=Inspection.Trend.Reason"): "",
        trend.get("drifting_camera_id", "ns=2;s=Inspection.Trend.DriftingCameraId"): "",
        trend.get("drift_score", "ns=2;s=Inspection.Trend.DriftScore"): 0.0,
        trend.get("score_delta", "ns=2;s=Inspection.Trend.ScoreDelta"): 0.0,
    }
