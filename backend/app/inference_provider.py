from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import base64
import hashlib
import os

import numpy as np


@dataclass
class InferenceOutput:
    anomaly_score: float
    status: str
    heatmap_uri: str
    model_version: str
    provider: str
    defect_class: str = "none"


class InferenceProvider(ABC):
    @abstractmethod
    def infer(self, frame: dict) -> InferenceOutput:
        raise NotImplementedError


def _hash_score(frame: dict, *, salt: str = "") -> float:
    fingerprint = f"{salt}{frame.get('frame_id','')}-{frame.get('camera_id','')}-{frame.get('recipe_id','')}"
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return round(int(digest[:8], 16) / 0xFFFFFFFF, 4)


def _synthetic_grayscale_image(frame: dict, size: int = 64):
    seed = int(hashlib.sha256(frame.get("frame_id", "x").encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    base = rng.normal(128, 25, (size, size)).astype("float32")
    return np.clip(base, 0, 255).astype("uint8")


def _frame_grayscale(frame: dict) -> np.ndarray:
    b64 = frame.get("image_b64")
    if b64:
        try:
            import cv2

            raw = base64.b64decode(b64)
            arr = np.frombuffer(raw, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                return img
        except Exception:
            pass

    uri = str(frame.get("image_uri", ""))
    if uri.startswith("file://"):
        try:
            import cv2

            # Restrict file:// reads to an allowlisted capture root (path traversal guard).
            raw_path = Path(uri[7:]).resolve()
            allowed_root = Path(
                os.getenv("FRAME_FILE_ROOT", str(Path(__file__).resolve().parents[1] / "data" / "frames"))
            ).resolve()
            if not str(raw_path).startswith(str(allowed_root) + os.sep) and raw_path != allowed_root:
                return _synthetic_grayscale_image(frame)
            img = cv2.imread(str(raw_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                return img
        except Exception:
            pass

    return _synthetic_grayscale_image(frame)


def _opencv_texture_score_from_gray(gray: np.ndarray) -> float | None:
    try:
        import cv2
    except ImportError:
        return None
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(np.var(laplacian))
    return round(min(1.0, variance / 2500.0), 4)


def _opencv_texture_score(frame: dict) -> float | None:
    return _opencv_texture_score_from_gray(_frame_grayscale(frame))


class StubInferenceProvider(InferenceProvider):
    def infer(self, frame: dict) -> InferenceOutput:
        score = _hash_score(frame)
        is_anomaly = score >= 0.7
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if is_anomaly else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version="patchcore-mvp-v0",
            provider="stub",
            defect_class="surface_defect" if is_anomaly else "none",
        )


class OpenCvReadyInferenceProvider(InferenceProvider):
    def infer(self, frame: dict) -> InferenceOutput:
        score = _opencv_texture_score(frame)
        if score is None:
            score = _hash_score(frame, salt="opencv-fallback-")
        is_anomaly = score >= 0.55
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if is_anomaly else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version="opencv-ready-v1",
            provider="opencv_ready",
            defect_class="edge_burr" if is_anomaly else "none",
        )


class PatchCoreInferenceProvider(InferenceProvider):
    """PatchCore with optional trained memory bank (embedding distance)."""

    def __init__(self) -> None:
        self._bank: np.ndarray | None = None
        self._model_version = "patchcore-v1"
        self._load_memory_bank()

    def _load_memory_bank(self) -> None:
        from .patchcore_memory import load_memory_bank

        custom = os.getenv("PATCHCORE_MEMORY_BANK", "").strip()
        candidates = []
        if custom:
            candidates.append(Path(custom))
        data_root = Path(__file__).resolve().parents[1] / "data" / "training-artifacts"
        candidates.append(data_root / "active_memory_bank.npz")
        for path in candidates:
            if path.exists():
                bank, meta = load_memory_bank(path)
                self._bank = bank
                self._model_version = meta.get("model_version", "patchcore-trained")
                return

    def infer(self, frame: dict) -> InferenceOutput:
        score = self._patchcore_score(frame)
        is_anomaly = score >= 0.6
        defect = "seam_void" if score >= 0.8 else ("edge_burr" if is_anomaly else "none")
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if is_anomaly else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version=self._model_version,
            provider="patchcore",
            defect_class=defect,
        )

    def _patchcore_score(self, frame: dict) -> float:
        if self._bank is not None:
            from .patchcore_memory import distance_to_anomaly_score, extract_embedding, min_distance_score

            gray = _frame_grayscale(frame)
            features = extract_embedding(gray)
            distance = min_distance_score(features, self._bank)
            bank_score = distance_to_anomaly_score(distance)
            return bank_score

        cv_score = _opencv_texture_score(frame)
        meta_score = _hash_score(frame, salt="patchcore-bank-")
        if cv_score is None:
            return meta_score
        combined = 0.65 * cv_score + 0.35 * meta_score
        return round(min(1.0, combined), 4)


def get_inference_provider() -> InferenceProvider:
    name = os.getenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub").strip().lower()
    if name in {"patchcore", "patch_core"}:
        return PatchCoreInferenceProvider()
    if name in {"opencv", "opencv_ready", "real"}:
        return OpenCvReadyInferenceProvider()
    return StubInferenceProvider()
