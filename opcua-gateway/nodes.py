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
        insp.get("camera_id", "ns=2;s=Inspection.Request.CameraId"): "cam-01",
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
        c["trend_warning"]: False,
    }
