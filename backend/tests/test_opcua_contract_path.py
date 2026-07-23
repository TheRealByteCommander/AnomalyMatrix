from pathlib import Path

from app.opcua_nodes import load_opcua_contract, node


def test_opcua_contract_loads_from_repo():
    contract = load_opcua_contract()
    assert "inspection" in contract or "last_result" in contract or any(
        isinstance(v, str) for v in contract.values()
    )


def test_opcua_node_resolution_smoke():
    # Common paths used by publish path — must not raise FileNotFoundError
    busy = node("inspection.busy")
    assert isinstance(busy, str) and busy
    score = node("last_result.anomaly_score")
    assert isinstance(score, str) and score


def test_contract_candidates_include_container_layout():
    from app import opcua_nodes

    candidates = opcua_nodes._contract_candidates()
    assert any(p.name == "opcua_nodeset_mapping_v1.json" for p in candidates)
    # At least one candidate must exist in this workspace
    assert any(p.exists() for p in candidates), candidates
