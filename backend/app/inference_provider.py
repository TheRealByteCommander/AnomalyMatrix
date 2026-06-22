from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib
import os


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
    """Deterministic grayscale patch from frame metadata (stand-in until real camera frames)."""
    import numpy as np

    seed = int(hashlib.sha256(frame.get("frame_id", "x").encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    base = rng.normal(128, 25, (size, size)).astype("float32")
    return np.clip(base, 0, 255).astype("uint8")


def _opencv_texture_score(frame: dict) -> float | None:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    gray = _synthetic_grayscale_image(frame)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(np.var(laplacian))
    # Normalize to 0..1 — higher texture variance => higher anomaly proxy
    return round(min(1.0, variance / 2500.0), 4)


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
    """Real-path baseline: OpenCV Laplacian texture analysis on synthetic frame patch."""

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
    """PatchCore-style MVP: memory-bank distance proxy via OpenCV feature spread + hash fallback."""

    def infer(self, frame: dict) -> InferenceOutput:
        score = self._patchcore_score(frame)
        is_anomaly = score >= 0.6
        defect = "seam_void" if score >= 0.8 else ("edge_burr" if is_anomaly else "none")
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if is_anomaly else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version="patchcore-v1",
            provider="patchcore",
            defect_class=defect,
        )

    def _patchcore_score(self, frame: dict) -> float:
        cv_score = _opencv_texture_score(frame)
        meta_score = _hash_score(frame, salt="patchcore-bank-")
        if cv_score is None:
            return meta_score
        # Combine texture anomaly with metadata fingerprint (simulates embedding distance)
        combined = 0.65 * cv_score + 0.35 * meta_score
        return round(min(1.0, combined), 4)


def get_inference_provider() -> InferenceProvider:
    name = os.getenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub").strip().lower()
    if name in {"patchcore", "patch_core"}:
        return PatchCoreInferenceProvider()
    if name in {"opencv", "opencv_ready", "real"}:
        return OpenCvReadyInferenceProvider()
    return StubInferenceProvider()
