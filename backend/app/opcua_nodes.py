from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _contract_candidates() -> list[Path]:
    here = Path(__file__).resolve()
    return [
        here.parents[2] / "contracts" / "opcua_nodeset_mapping_v1.json",  # repo root (dev)
        here.parents[1] / "contracts" / "opcua_nodeset_mapping_v1.json",  # /app/contracts (container)
        Path("/contracts/opcua_nodeset_mapping_v1.json"),
    ]


@lru_cache(maxsize=1)
def load_opcua_contract() -> dict:
    for path in _contract_candidates():
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    searched = ", ".join(str(p) for p in _contract_candidates())
    raise FileNotFoundError(f"opcua_nodeset_mapping_v1.json not found (tried: {searched})")


def node(path: str) -> str:
    """Resolve dotted path, e.g. inspection.busy or last_result.pass_fail."""
    contract = load_opcua_contract()
    if path in contract and isinstance(contract[path], str):
        return contract[path]
    parts = path.split(".")
    cur: object = contract
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"Unknown OPC UA node path: {path}")
        cur = cur[part]
    if not isinstance(cur, str):
        raise KeyError(f"OPC UA node path is not a string: {path}")
    return cur


def all_result_node_ids() -> list[str]:
    contract = load_opcua_contract()
    ids = list(contract.get("last_result", {}).values())
    insp = contract.get("inspection", {})
    for key in ("busy", "stop_line_request", "reject_part", "result_ready"):
        if key in insp:
            ids.append(insp[key])
    if "trend_warning" in contract:
        ids.append(contract["trend_warning"])
    for value in (contract.get("trend") or {}).values():
        if isinstance(value, str):
            ids.append(value)
    if "system_state" in contract:
        ids.append(contract["system_state"])
    return ids
