from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from nodes import build_default_node_values, load_contract
from plc_bridge import get_plc_bridge
from security_config import apply_server_security

logger = logging.getLogger(__name__)

NODE_VALUES: dict[str, object] = build_default_node_values()
_server_task: asyncio.Task | None = None
_ua_vars: dict[str, object] = {}


def apply_payload(payload: dict) -> int:
    count = 0
    for key, value in payload.items():
        NODE_VALUES[key] = value
        count += 1
    contract = load_contract()
    ts_key = contract["last_result"].get("timestamp", "ns=2;s=Inspection.LastResult.Timestamp")
    NODE_VALUES[ts_key] = datetime.now(timezone.utc).isoformat()
    return count


async def _sync_vars_from_store() -> None:
    for node_key, var in _ua_vars.items():
        value = NODE_VALUES.get(node_key, "")
        try:
            await var.write_value(value)
        except Exception:
            pass


async def _sync_store_from_plc_inputs() -> None:
    """Read PLC-written input nodes back into NODE_VALUES."""
    contract = load_contract()
    insp = contract["inspection"]
    input_keys = ("external_trigger", "start_request", "acknowledge_stop", "camera_id", "recipe_id")
    for key in input_keys:
        nid = insp[key]
        var = _ua_vars.get(nid)
        if var is not None:
            try:
                NODE_VALUES[nid] = await var.read_value()
            except Exception:
                pass


async def _run_opcua_server(endpoint: str) -> None:
    try:
        from asyncua import Server, ua
    except ImportError:
        logger.warning("asyncua not installed — OPC UA server disabled")
        return

    contract = load_contract()
    insp = contract["inspection"]
    lr = contract["last_result"]
    bridge = get_plc_bridge()

    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name("AnomalyMatrix OPC UA Gateway")
    security = await apply_server_security(server)
    if security.get("enabled"):
        logger.info("OPC-UA security enabled: %s", security.get("mode"))

    uri = contract.get("namespace_uri", "http://anomalymatrix.local/opcua")
    idx = await server.register_namespace(uri)
    objects = server.nodes.objects

    system = await objects.add_object(idx, "System")
    inspection = await objects.add_object(idx, "Inspection")
    last_result = await inspection.add_object(idx, "LastResult")
    request = await inspection.add_object(idx, "Request")
    recipe = await objects.add_object(idx, "Recipe")

    global _ua_vars
    _ua_vars = {}

    async def add_var(parent, name, node_key, vtype, writable=False):
        initial = NODE_VALUES.get(node_key, "")
        if vtype == ua.VariantType.Double:
            initial = float(NODE_VALUES.get(node_key, 0.0))
        elif vtype == ua.VariantType.Boolean:
            initial = bool(NODE_VALUES.get(node_key, False))
        elif vtype == ua.VariantType.Int32:
            initial = int(NODE_VALUES.get(node_key, 0))
        var = await parent.add_variable(idx, name, initial, varianttype=vtype)
        if writable:
            await var.set_writable()
        _ua_vars[node_key] = var
        return var

    await add_var(system, "State", contract["system_state"], ua.VariantType.String)
    await add_var(system, "Health", contract.get("system_health", "ns=2;s=System.Health"), ua.VariantType.String)
    await add_var(recipe, "Active", contract["active_recipe"], ua.VariantType.String)

    await add_var(inspection, "Busy", insp["busy"], ua.VariantType.Boolean)
    await add_var(inspection, "ExternalTrigger", insp["external_trigger"], ua.VariantType.Boolean, writable=True)
    await add_var(inspection, "StartRequest", insp["start_request"], ua.VariantType.Boolean, writable=True)
    await add_var(inspection, "AcknowledgeStop", insp["acknowledge_stop"], ua.VariantType.Boolean, writable=True)
    await add_var(inspection, "StopLineRequest", insp["stop_line_request"], ua.VariantType.Boolean)
    await add_var(inspection, "RejectPart", insp["reject_part"], ua.VariantType.Boolean)
    await add_var(inspection, "ResultReady", insp["result_ready"], ua.VariantType.Boolean)
    await add_var(inspection, "TrendWarning", contract["trend_warning"], ua.VariantType.Boolean)

    await add_var(request, "CameraId", insp["camera_id"], ua.VariantType.String, writable=True)
    await add_var(request, "RecipeId", insp["recipe_id"], ua.VariantType.String, writable=True)

    await add_var(last_result, "PassFail", lr["pass_fail"], ua.VariantType.String)
    await add_var(last_result, "PassFailBool", lr["pass_fail_bool"], ua.VariantType.Boolean)
    await add_var(last_result, "AnomalyScore", lr["anomaly_score"], ua.VariantType.Double)
    await add_var(last_result, "DefectClass", lr["defect_class"], ua.VariantType.String)
    await add_var(last_result, "DecisionCode", lr["decision_code"], ua.VariantType.Int32)
    await add_var(last_result, "HeatmapUri", lr["heatmap_uri"], ua.VariantType.String)
    await add_var(last_result, "ModelVersion", lr["model_version"], ua.VariantType.String)
    await add_var(last_result, "InspectionId", lr["inspection_id"], ua.VariantType.String)
    await add_var(last_result, "Timestamp", lr["timestamp"], ua.VariantType.String)

    async def start_inspection_handler(parent, camera_id: str, recipe_id: str):
        await _sync_store_from_plc_inputs()
        ok = await bridge.run_method(NODE_VALUES, camera_id, recipe_id)
        await _sync_vars_from_store()
        return [ua.Variant(ok, ua.VariantType.Boolean)]

    await inspection.add_method(
        idx,
        "StartInspection",
        start_inspection_handler,
        [ua.VariantType.String, ua.VariantType.String],
        [ua.VariantType.Boolean],
    )

    async with server:
        logger.info("OPC UA server listening on %s (PLC trigger + StopLine/Reject outputs)", endpoint)
        while True:
            await _sync_store_from_plc_inputs()
            await bridge.process_tick(NODE_VALUES)
            await _sync_vars_from_store()
            await asyncio.sleep(0.25)


def start_opcua_background(endpoint: str) -> asyncio.Task:
    global _server_task
    if _server_task is None or _server_task.done():
        _server_task = asyncio.create_task(_run_opcua_server(endpoint))
    return _server_task


async def stop_opcua_background() -> None:
    global _server_task
    if _server_task and not _server_task.done():
        _server_task.cancel()
        try:
            await _server_task
        except asyncio.CancelledError:
            pass
    _server_task = None
