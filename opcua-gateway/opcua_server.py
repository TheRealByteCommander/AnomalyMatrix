from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-process node value store (updated by HTTP /publish and readable via OPC UA)
NODE_VALUES: dict[str, object] = {
    "ns=2;s=Inspection.LastResult.PassFail": "unknown",
    "ns=2;s=Inspection.LastResult.AnomalyScore": 0.0,
    "ns=2;s=Inspection.LastResult.DefectClass": "none",
    "ns=2;s=Inspection.LastResult.HeatmapUri": "",
    "ns=2;s=Inspection.LastResult.ModelVersion": "",
    "ns=2;s=Inspection.LastResult.InspectionId": "",
    "ns=2;s=Inspection.LastResult.Timestamp": "",
    "ns=2;s=Inspection.Trend.Warning": False,
}

_server_task: asyncio.Task | None = None


def apply_payload(payload: dict) -> int:
    count = 0
    for key, value in payload.items():
        NODE_VALUES[key] = value
        count += 1
    NODE_VALUES["ns=2;s=Inspection.LastResult.Timestamp"] = datetime.now(timezone.utc).isoformat()
    return count


async def _run_opcua_server(endpoint: str) -> None:
    try:
        from asyncua import Server, ua
    except ImportError:
        logger.warning("asyncua not installed — OPC UA server disabled")
        return

    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    server.set_server_name("AnomalyMatrix OPC UA Gateway")

    uri = "http://anomalymatrix.local/opcua"
    idx = await server.register_namespace(uri)
    objects = server.nodes.objects
    inspection = await objects.add_object(idx, "Inspection")
    last_result = await inspection.add_object(idx, "LastResult")

    # Variable nodes mapped to NODE_VALUES keys
    var_map = {
        "PassFail": ("ns=2;s=Inspection.LastResult.PassFail", ua.VariantType.String),
        "AnomalyScore": ("ns=2;s=Inspection.LastResult.AnomalyScore", ua.VariantType.Double),
        "DefectClass": ("ns=2;s=Inspection.LastResult.DefectClass", ua.VariantType.String),
        "HeatmapUri": ("ns=2;s=Inspection.LastResult.HeatmapUri", ua.VariantType.String),
        "ModelVersion": ("ns=2;s=Inspection.LastResult.ModelVersion", ua.VariantType.String),
        "InspectionId": ("ns=2;s=Inspection.LastResult.InspectionId", ua.VariantType.String),
        "Timestamp": ("ns=2;s=Inspection.LastResult.Timestamp", ua.VariantType.String),
    }
    ua_vars = {}
    for name, (node_key, vtype) in var_map.items():
        initial = NODE_VALUES.get(node_key, "")
        if vtype == ua.VariantType.Double:
            initial = float(NODE_VALUES.get(node_key, 0.0))
        var = await last_result.add_variable(idx, name, initial, varianttype=vtype)
        await var.set_writable()
        ua_vars[node_key] = var

    trend_var = await inspection.add_variable(idx, "TrendWarning", False, varianttype=ua.VariantType.Boolean)
    await trend_var.set_writable()
    ua_vars["ns=2;s=Inspection.Trend.Warning"] = trend_var

    async with server:
        logger.info("OPC UA server listening on %s", endpoint)
        while True:
            for node_key, var in ua_vars.items():
                value = NODE_VALUES.get(node_key, "")
                try:
                    await var.write_value(value)
                except Exception:
                    pass
            await asyncio.sleep(0.5)


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
