import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_run_inspection_latency_under_500ms(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub")
    started = time.perf_counter()
    response = client.post(
        "/api/v1/inspections/run",
        json={"camera_id": "perf-cam", "recipe_id": "recipe-default"},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert response.status_code == 200
    assert elapsed_ms < 500, f"inspection run took {elapsed_ms:.1f} ms"


def test_patchcore_infer_latency_under_500ms(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "patchcore")
    started = time.perf_counter()
    response = client.post(
        "/api/v1/ai/infer",
        json={"frame_id": "perf-f", "camera_id": "cam-01", "recipe_id": "recipe-default"},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert response.status_code == 200
    assert elapsed_ms < 500, f"infer took {elapsed_ms:.1f} ms"
