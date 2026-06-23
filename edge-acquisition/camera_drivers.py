from __future__ import annotations

import base64
import os
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class CameraDriver(ABC):
    @abstractmethod
    def capture(self, *, camera_id: str, recipe_id: str) -> tuple[np.ndarray, dict]:
        raise NotImplementedError


class SyntheticCameraDriver(CameraDriver):
    def capture(self, *, camera_id: str, recipe_id: str) -> tuple[np.ndarray, dict]:
        seed = abs(hash(f"{camera_id}:{recipe_id}")) % (2**31)
        rng = np.random.default_rng(seed)
        image = np.clip(rng.normal(128, 18, (256, 256)), 0, 255).astype(np.uint8)
        return image, {"driver": "synthetic", "exposure_ms": 10.0, "gain_db": 0.0}


class OpenCvCameraDriver(CameraDriver):
    """OpenCV capture from webcam index, video file, or still image path."""

    def capture(self, *, camera_id: str, recipe_id: str) -> tuple[np.ndarray, dict]:
        import cv2

        source = os.getenv("CAMERA_SOURCE", camera_id).strip()
        meta = {"driver": "opencv", "source": source, "exposure_ms": 10.0, "gain_db": 0.0}

        if source.isdigit():
            cap = cv2.VideoCapture(int(source))
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                raise RuntimeError(f"Webcam {source} capture failed")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
            return gray.astype(np.uint8), meta

        path = Path(source)
        if path.exists():
            frame = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if frame is None:
                raise RuntimeError(f"Could not read image: {path}")
            return frame.astype(np.uint8), meta

        raise RuntimeError(f"Camera source not found: {source}")


def get_camera_driver() -> CameraDriver:
    mode = os.getenv("CAMERA_DRIVER", "synthetic").strip().lower()
    if mode in {"opencv", "webcam", "file", "real"}:
        return OpenCvCameraDriver()
    return SyntheticCameraDriver()


def encode_image_b64(image: np.ndarray) -> str:
    import cv2

    if image.ndim == 2:
        ok, buf = cv2.imencode(".png", image)
    else:
        ok, buf = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("PNG encode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")
