from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_vertical_run_inspection_and_fetch_latest():
    run = client.post('/api/v1/orchestrate/run-inspection', json={'camera_id': 'cam-a', 'recipe_id': 'recipe-1'})
    assert run.status_code == 200
    body = run.json()
    assert body['ok'] is True
    assert body['data']['frame']['camera_id'] == 'cam-a'
    assert 'anomaly_score' in body['data']['inference']

    latest = client.get('/api/v1/results/latest')
    assert latest.status_code == 200
    payload = latest.json()
    assert payload['ok'] is True
    assert payload['data']['count'] >= 1


def test_edge_capture_and_ai_infer_stubs():
    cap = client.post('/api/v1/edge/capture', json={'camera_id': 'cam-x', 'recipe_id': 'r-x'})
    assert cap.status_code == 200
    frame = cap.json()['data']

    inf = client.post('/api/v1/ai/infer', json={'frame_id': frame['frame_id'], 'camera_id': frame['camera_id'], 'recipe_id': frame['recipe_id']})
    assert inf.status_code == 200
    out = inf.json()['data']
    assert 0 <= out['anomaly_score'] <= 1
    assert out['heatmap_uri'].startswith('synthetic://heatmap/')
