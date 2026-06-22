from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from inspection_client import run_inspection_sync
from nodes import load_contract

logger = logging.getLogger(__name__)

_plc_bridge: "PlcBridge | None" = None


class PlcBridge:
    """PLC inputs: ExternalTrigger, StartRequest, AcknowledgeStop → inspection / clear stop."""

    def __init__(self) -> None:
        self._last_external = False
        self._last_start = False
        self._running = False
        self._contract = load_contract()
        self._insp = self._contract["inspection"]

    def _nid(self, key: str) -> str:
        return self._insp[key]

    async def process_tick(self, node_values: dict) -> None:
        external = bool(node_values.get(self._nid("external_trigger"), False))
        start_req = bool(node_values.get(self._nid("start_request"), False))
        ack_stop = bool(node_values.get(self._nid("acknowledge_stop"), False))

        if ack_stop:
            node_values[self._nid("acknowledge_stop")] = False
            node_values[self._nid("stop_line_request")] = False
            node_values[self._nid("reject_part")] = False
            logger.info("PLC acknowledged stop — cleared StopLineRequest and RejectPart")

        rising = (external and not self._last_external) or (start_req and not self._last_start)
        self._last_external = external
        self._last_start = start_req

        if rising and not self._running:
            camera = str(node_values.get(self._nid("camera_id"), "cam-01"))
            recipe = str(node_values.get(self._nid("recipe_id"), "recipe-default"))
            node_values[self._nid("external_trigger")] = False
            node_values[self._nid("start_request")] = False
            await self._run_inspection(node_values, camera, recipe)

    async def run_method(self, node_values: dict, camera_id: str, recipe_id: str) -> bool:
        if self._running:
            return False
        return await self._run_inspection(node_values, camera_id or "cam-01", recipe_id or "recipe-default")

    async def _run_inspection(self, node_values: dict, camera_id: str, recipe_id: str) -> bool:
        if self._running:
            return False
        self._running = True
        try:
            node_values[self._nid("busy")] = True
            node_values[self._nid("result_ready")] = False
            node_values[self._contract["system_state"]] = "busy"
            node_values[self._contract.get("system_health", "ns=2;s=System.Health")] = "ok"

            logger.info("OPC UA inspection trigger camera=%s recipe=%s", camera_id, recipe_id)
            result = await asyncio.to_thread(
                run_inspection_sync,
                camera_id=camera_id,
                recipe_id=recipe_id,
            )
            if not result:
                node_values[self._contract["system_state"]] = "error"
                node_values[self._contract.get("system_health", "ns=2;s=System.Health")] = "api_error"
                return False
            return True
        finally:
            self._running = False


def get_plc_bridge() -> PlcBridge:
    global _plc_bridge
    if _plc_bridge is None:
        _plc_bridge = PlcBridge()
    return _plc_bridge
