from app.opcua_nodes import load_opcua_contract, node
from app.opcua_publish import map_inspection_to_opcua_payload


def test_opcua_contract_v12_has_plc_and_multiview_nodes():
    contract = load_opcua_contract()
    assert contract["version"] == "1.2.0"
    assert "stop_line_request" in contract["inspection"]
    assert "external_trigger" in contract["inspection"]
    assert "decision_code" in contract["last_result"]
    assert "worst_view_camera_id" in contract["last_result"]
    assert "view_count" in contract["last_result"]
    assert "drifting_camera_id" in contract["trend"]


def test_opcua_payload_includes_multiview_and_drift():
    mapped = map_inspection_to_opcua_payload(
        {
            "inspection_id": "insp-mv",
            "decision": "amber",
            "camera_ids": ["cam-01", "cam-02"],
            "view_count": 2,
            "worst_view_camera_id": "cam-02",
            "decision_policy": "worst_view",
            "trend_warning": True,
            "trend_severity": "amber",
            "trend_reason": "camera_drift:cam-02:rising_vs_baseline",
            "drifting_camera_id": "cam-02",
            "drift_score": 1.2,
            "score_delta": 0.25,
            "frame": {"recipe_id": "recipe-A", "camera_id": "cam-02"},
            "inference": {"status": "anomaly", "anomaly_score": 0.6, "heatmap_uri": "h", "model_version": "m"},
        }
    )
    assert mapped[node("last_result.view_count")] == 2
    assert mapped[node("last_result.camera_ids")] == "cam-01,cam-02"
    assert mapped[node("last_result.worst_view_camera_id")] == "cam-02"
    assert mapped[node("trend.drifting_camera_id")] == "cam-02"
    assert mapped[node("trend.warning")] is True


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
