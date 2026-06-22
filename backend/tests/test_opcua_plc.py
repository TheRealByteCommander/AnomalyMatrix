from app.opcua_nodes import load_opcua_contract, node
from app.opcua_publish import map_inspection_to_opcua_payload


def test_opcua_contract_v11_has_plc_nodes():
    contract = load_opcua_contract()
    assert contract["version"] == "1.1.0"
    assert "stop_line_request" in contract["inspection"]
    assert "external_trigger" in contract["inspection"]
    assert "decision_code" in contract["last_result"]


def test_opcua_payload_stop_on_red():
    mapped = map_inspection_to_opcua_payload(
        {
            "inspection_id": "insp-red",
            "decision": "red",
            "frame": {"recipe_id": "recipe-A"},
            "inference": {
                "status": "anomaly",
                "anomaly_score": 0.92,
                "defect_class": "seam_void",
                "heatmap_uri": "h",
                "model_version": "m",
            },
        }
    )
    assert mapped[node("inspection.stop_line_request")] is True
    assert mapped[node("inspection.reject_part")] is True
    assert mapped[node("last_result.decision_code")] == 2
    assert mapped[node("last_result.pass_fail_bool")] is False
    assert mapped[node("inspection.result_ready")] is True


def test_opcua_payload_green_no_stop():
    mapped = map_inspection_to_opcua_payload(
        {
            "inspection_id": "insp-ok",
            "decision": "green",
            "inference": {"status": "normal", "anomaly_score": 0.1},
        }
    )
    assert mapped[node("inspection.stop_line_request")] is False
    assert mapped[node("inspection.reject_part")] is False
    assert mapped[node("last_result.decision_code")] == 0
    assert mapped[node("last_result.pass_fail_bool")] is True


def test_opcua_payload_amber_review_code():
    mapped = map_inspection_to_opcua_payload(
        {
            "decision": "amber",
            "inference": {"status": "anomaly", "anomaly_score": 0.6},
        }
    )
    assert mapped[node("last_result.decision_code")] == 1
    assert mapped[node("inspection.stop_line_request")] is False
