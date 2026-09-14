from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app import main as main_module
from app.core_store import CoreStore
from app.event_bus import DomainEventBus
from app.heatmap import generate_heatmap_png
from app.inference_provider import PatchCoreInferenceProvider
from app.main import app
from app.patchcore_memory import (
    LAYOUT_IMAGE,
    build_memory_bank,
    extract_embedding,
    infer_spatial,
    load_memory_bank,
    save_memory_bank,
)
from app.repository import ResultRepository
from app.services_edge import SyntheticFrame
from app.training_service import set_active_memory_bank

client = TestClient(app)
ENGINEER = {"X-AMX-Role": "process_engineer", "X-AMX-User": "engineer-1"}
ADMIN = {"X-AMX-Role": "admin", "X-AMX-User": "admin-1"}

DEFECT_BOX = (42, 68, 78, 106)  # y0, y1, x0, x1 — damaged grille area


def _colorfulness(bgr: np.ndarray) -> float:
    """Mean chroma vs gray — jet hotspots are colorful, residual-gray is not."""
    b = bgr[:, :, 0].astype(np.float32)
    g = bgr[:, :, 1].astype(np.float32)
    r = bgr[:, :, 2].astype(np.float32)
    gray = (b + g + r) / 3.0
    return float(np.mean(np.abs(r - gray) + np.abs(g - gray) + np.abs(b - gray)))


def _good_part(*, size: int = 128, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.full((size, size), 90, dtype=np.uint8)
    img[40:70, 20:108] = 140  # bright grille band
    noise = rng.integers(-3, 4, img.shape, dtype=np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def _defective_part(*, size: int = 128) -> np.ndarray:
    img = _good_part(size=size, seed=99)
    y0, y1, x0, x1 = DEFECT_BOX
    img[y0:y1, x0:x1] = 18  # dark gouge on the right grille
    return img


def _png_b64(gray: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", gray)
    assert ok
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _bind(tmp_path, monkeypatch, *, provider: str = "patchcore"):
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("ANOMALYMATRIX_INFERENCE_PROVIDER", provider)
    store = CoreStore(tmp_path)
    bus = DomainEventBus(tmp_path)
    repo = ResultRepository(tmp_path)
    app.state.core_store = store
    app.state.event_bus = bus
    app.state.repo = repo
    main_module.core_store = store
    main_module.event_bus = bus
    main_module.repo = repo
    return store, repo


def test_patch_heatmap_hotspot_on_defect_not_edges():
    goods = [_good_part(seed=i) for i in range(8)]
    bank = build_memory_bank(goods)
    defect = _defective_part()
    score, amap, kind = infer_spatial(defect, bank, {"layout": "patch_grid", "grid": 16, "patch_embed_size": 16})
    assert kind == "patchcore"
    assert amap is not None
    assert amap.shape == defect.shape
    assert 0.0 <= score <= 1.0

    y0, y1, x0, x1 = DEFECT_BOX
    peak_y, peak_x = np.unravel_index(int(np.argmax(amap)), amap.shape)
    assert y0 - 12 <= peak_y < y1 + 12
    assert x0 - 12 <= peak_x < x1 + 12

    defect_mean = float(amap[y0:y1, x0:x1].mean())
    quiet_mean = float(amap[8:36, 8:36].mean())
    assert defect_mean > quiet_mean * 1.8

    # Interior of the gouge (not just its edges) must be hot — residual would be cold inside.
    interior = float(amap[y0 + 4 : y1 - 4, x0 + 4 : x1 - 4].mean())
    assert interior > quiet_mean * 1.8

    png = generate_heatmap_png(defect, score, anomaly_map=amap)
    assert png.startswith(b"\x89PNG")
    overlay = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert overlay is not None
    assert _colorfulness(overlay[y0:y1, x0:x1]) > _colorfulness(overlay[8:36, 8:36]) * 1.5


def test_legacy_image_bank_still_loads_and_is_model_based(tmp_path):
    goods = [_good_part(seed=i) for i in range(4)]
    rows = [extract_embedding(img) for img in goods]
    legacy = tmp_path / "legacy_bank.npz"
    np.savez_compressed(
        legacy,
        embeddings=np.stack(rows, axis=0),
        model_version=np.asarray("legacy-v0"),
        recipe_id=np.asarray("recipe-default"),
    )
    bank, meta = load_memory_bank(legacy)
    assert meta["layout"] == LAYOUT_IMAGE
    score, amap, kind = infer_spatial(_defective_part(), bank, meta)
    assert kind == "legacy_spatial"
    assert amap is not None
    assert 0.0 <= score <= 1.0


def test_new_bank_roundtrip_is_patch_grid(tmp_path):
    bank = build_memory_bank([_good_part(seed=1), _good_part(seed=2)])
    path = tmp_path / "bank.npz"
    save_memory_bank(path, bank=bank, model_version="v-test", recipe_id="recipe-default")
    loaded, meta = load_memory_bank(path)
    assert meta["layout"] == "patch_grid"
    assert loaded.shape[0] == 2 * 16 * 16
    assert loaded.shape[1] == 16 * 16


def test_residual_heatmap_is_last_resort_without_bank():
    gray = _defective_part()
    png = generate_heatmap_png(gray, 0.8, anomaly_map=None)
    assert png.startswith(b"\x89PNG")


def test_inspection_returns_non_placeholder_model_heatmap_when_bank_present(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch, provider="patchcore")
    goods = [_good_part(seed=i) for i in range(8)]
    bank = build_memory_bank(goods)
    artifact = tmp_path / "training-artifacts" / "patchcore-heatmap.npz"
    save_memory_bank(artifact, bank=bank, model_version="heatmap-test", recipe_id="recipe-default")
    set_active_memory_bank(tmp_path, artifact)

    defect = _defective_part()

    def _capture(*, camera_id, recipe_id, source=None):
        return SyntheticFrame(
            frame_id="frame-defect",
            camera_id=camera_id,
            recipe_id=recipe_id,
            captured_at="2026-09-14T00:00:00+00:00",
            image_uri="synthetic://frame/defect.png",
            exposure_ms=8.0,
            gain_db=1.0,
            image_b64=_png_b64(defect),
            image_width=128,
            image_height=128,
            capture_driver="synthetic",
            source=source or f"synthetic:{camera_id}",
        )

    monkeypatch.setattr("app.main.capture_frame", _capture)

    run = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"})
    assert run.status_code == 200
    payload = run.json()["data"]
    heatmap = payload["heatmap"]
    assert heatmap["placeholder"] is False
    assert heatmap["kind"] == "patchcore"
    assert heatmap["model_based"] is True
    assert payload["inference"]["heatmap_kind"] == "patchcore"
    assert payload["memory_bank"]["loaded"] is True
    assert payload["memory_bank"]["localization_ready"] is True

    inspection_id = payload["inspection_id"]
    png = client.get(f"/api/v1/inspections/{inspection_id}/heatmap")
    assert png.status_code == 200
    assert png.headers["content-type"].startswith("image/png")
    assert png.content.startswith(b"\x89PNG")
    overlay = cv2.imdecode(np.frombuffer(png.content, dtype=np.uint8), cv2.IMREAD_COLOR)
    y0, y1, x0, x1 = DEFECT_BOX
    assert _colorfulness(overlay[y0:y1, x0:x1]) > _colorfulness(overlay[8:36, 8:36]) * 1.5


def test_inspection_heatmap_residual_without_bank_is_labeled(tmp_path, monkeypatch):
    _bind(tmp_path, monkeypatch, provider="patchcore")
    run = client.post("/api/v1/inspections/run", json={"recipe_id": "recipe-default"})
    assert run.status_code == 200
    heatmap = run.json()["data"]["heatmap"]
    assert heatmap["placeholder"] is False
    assert heatmap["kind"] == "residual"
    assert heatmap["model_based"] is False


def test_patchcore_provider_uses_spatial_map_when_bank_loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("ANOMALYMATRIX_DATA_ROOT", str(tmp_path))
    goods = [_good_part(seed=i) for i in range(6)]
    artifact = Path(tmp_path) / "training-artifacts" / "active_memory_bank.npz"
    save_memory_bank(
        artifact,
        bank=build_memory_bank(goods),
        model_version="p",
        recipe_id="recipe-default",
    )
    provider = PatchCoreInferenceProvider()
    out = provider.infer({"frame_id": "f1", "camera_id": "cam-01", "recipe_id": "recipe-default", "image_b64": _png_b64(_defective_part())})
    assert out.heatmap_kind == "patchcore"
    assert out.anomaly_map is not None
    public = out.to_public_dict()
    assert "anomaly_map" not in public
    assert public["heatmap_kind"] == "patchcore"
