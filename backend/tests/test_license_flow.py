from fastapi.testclient import TestClient

from app.main import app, license_manager


def test_license_status_endpoint():
    client = TestClient(app)
    r = client.get('/api/v1/license/status')
    assert r.status_code == 200
    assert r.json()['ok'] is True


def test_license_gate_blocks_without_feature(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(license_manager, 'enforce_feature', lambda feature: (_ for _ in ()).throw(PermissionError('Missing feature')) if feature == 'inspection.run' else None)
    r = client.post('/api/v1/orchestrate/run-inspection', json={'camera_id': 'c', 'recipe_id': 'r'})
    assert r.status_code == 402


def test_activate_requires_admin_token(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv('LICENSE_ADMIN_TOKEN', 'secret')
    r = client.post('/api/v1/license/activate', json={'license_key': 'K'}, headers={'X-License-Admin-Token': 'wrong'})
    assert r.status_code == 403
