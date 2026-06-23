import concurrent.futures
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parallel_inspection_runs(monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub")

    def run_once():
        started = time.perf_counter()
        r = client.post(
            "/api/v1/inspections/run",
            json={"camera_id": "load-cam", "recipe_id": "recipe-default"},
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return r.status_code, elapsed_ms

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: run_once(), range(10)))

    assert all(code == 200 for code, _ in results)
    assert all(ms < 1000 for _, ms in results)
