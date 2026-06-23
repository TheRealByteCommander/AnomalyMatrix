import os
from fastapi.testclient import TestClient

from app.main import app
from app.inference_provider import get_inference_provider
from app.opcua_publish import map_inspection_to_opcua_payload

client = TestClient(app)


def test_provider_switching_env(monkeypatch):
    monkeypatch.setenv('ANOMALYMATRIX_INFERENCE_PROVIDER', 'opencv_ready')
    p = get_inference_provider()
    out = p.infer({'frame_id': 'a', 'camera_id': 'c', 'recipe_id': 'r'})
    assert out.provider == 'opencv_ready'


def test_run_inspection_includes_opcua_publish_block(monkeypatch):
    monkeypatch.setenv('ANOMALYMATRIX_INFERENCE_PROVIDER', 'stub')
    r = client.post('/api/v1/orchestrate/run-inspection', json={'camera_id': 'cam-z', 'recipe_id': 'recipe-z'})
    assert r.status_code == 200
    payload = r.json()['data']
    assert payload['opcua_publish']['published'] is True
    assert 'ns=2;s=Inspection.LastResult.AnomalyScore' in payload['opcua_publish']['payload'] or any(
        'AnomalyScore' in k for k in payload['opcua_publish']['payload']
    )


def test_results_query_by_recipe_and_score_range():
    # seed two results
    client.post('/api/v1/orchestrate/run-inspection', json={'camera_id': 'cam-1', 'recipe_id': 'recipe-A'})
    client.post('/api/v1/orchestrate/run-inspection', json={'camera_id': 'cam-2', 'recipe_id': 'recipe-B'})

    q = client.get('/api/v1/results/query', params={'recipe_id': 'recipe-A', 'min_score': 0.0, 'max_score': 1.0, 'limit': 50})
    assert q.status_code == 200
    body = q.json()['data']
    assert body['count'] >= 1
    assert all(item['frame']['recipe_id'] == 'recipe-A' for item in body['items'])


def test_trend_summary_endpoint():
    r = client.get('/api/v1/results/trend-summary')
    assert r.status_code == 200
    d = r.json()['data']
    assert {'count', 'avg_score', 'max_score', 'anomaly_count', 'trend_warning', 'trend_severity'} <= set(d.keys())


def test_opcua_payload_mapping_unit():
    mapped = map_inspection_to_opcua_payload({
        'inspection_id': 'x',
        'decision': 'red',
        'inference': {'status': 'anomaly', 'anomaly_score': 0.12, 'heatmap_uri': 'h', 'model_version': 'm', 'defect_class': 'seam_void'},
    })
    from app.opcua_nodes import node
    assert mapped[node('last_result.pass_fail')] == 'anomaly'
    assert mapped[node('last_result.anomaly_score')] == 0.12
    assert mapped[node('last_result.defect_class')] == 'seam_void'
    assert mapped[node('inspection.stop_line_request')] is True
