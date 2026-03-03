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


class InferenceProvider(ABC):
    @abstractmethod
    def infer(self, frame: dict) -> InferenceOutput:
        raise NotImplementedError


class StubInferenceProvider(InferenceProvider):
    def infer(self, frame: dict) -> InferenceOutput:
        fingerprint = f"{frame.get('frame_id','')}-{frame.get('camera_id','')}-{frame.get('recipe_id','')}"
        digest = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
        score_raw = int(digest[:8], 16) / 0xFFFFFFFF
        score = round(score_raw, 4)
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if score >= 0.7 else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version="patchcore-mvp-v0",
            provider="stub",
        )


class OpenCvReadyInferenceProvider(InferenceProvider):
    """Baseline real-path provider that can use OpenCV/PyTorch when available.

    For MVP it computes a deterministic score from frame metadata and marks provider as `opencv_ready`.
    """

    def infer(self, frame: dict) -> InferenceOutput:
        # placeholder-real logic: deterministic but explicitly separated provider for future CV model wiring
        fingerprint = f"real-{frame.get('frame_id','')}-{frame.get('camera_id','')}-{frame.get('recipe_id','')}"
        digest = hashlib.sha1(fingerprint.encode('utf-8')).hexdigest()
        score = round(int(digest[:8], 16) / 0xFFFFFFFF, 4)
        return InferenceOutput(
            anomaly_score=score,
            status="anomaly" if score >= 0.7 else "normal",
            heatmap_uri=f"synthetic://heatmap/{frame.get('frame_id','unknown')}.png",
            model_version="opencv-ready-v0",
            provider="opencv_ready",
        )


def get_inference_provider() -> InferenceProvider:
    name = os.getenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub").strip().lower()
    if name in {"opencv", "opencv_ready", "real"}:
        return OpenCvReadyInferenceProvider()
    return StubInferenceProvider()
