from __future__ import annotations

import base64
import os
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from camera_discover import resolve_source
from gige_backend import GigEUnavailableError, grab_gige_frame, is_gige_driver


class CameraDriver(ABC):
    @abstractmethod
    def capture(self, *, camera_id: str, recipe_id: str, source: str | None = None) -> tuple[np.ndarray, dict]:
        raise NotImplementedError


class SyntheticCameraDriver(CameraDriver):
    def capture(self, *, camera_id: str, recipe_id: str, source: str | None = None) -> tuple[np.ndarray, dict]:
        seed = abs(hash(f"{camera_id}:{recipe_id}:{source or ''}")) % (2**31)
        rng = np.random.default_rng(seed)
        image = np.clip(rng.normal(128, 18, (256, 256)), 0, 255).astype(np.uint8)
        return image, {
            "driver": "synthetic",
            "source": source or f"synthetic:{camera_id}",
            "exposure_ms": 10.0,
            "gain_db": 0.0,
            "trigger_mode": "freerun",
        }


class OpenCvCameraDriver(CameraDriver):
    """OpenCV capture from webcam index, video file, or still image path."""

    def capture(self, *, camera_id: str, recipe_id: str, source: str | None = None) -> tuple[np.ndarray, dict]:
        import cv2

        resolved = resolve_source(camera_id=camera_id, source=source)
        if not resolved:
            resolved = os.getenv("CAMERA_SOURCE", "0").strip()
        meta = {
            "driver": "opencv",
            "source": resolved,
            "exposure_ms": 10.0,
            "gain_db": 0.0,
            "trigger_mode": "freerun",
        }

        if resolved.isdigit():
            cap = cv2.VideoCapture(int(resolved))
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                raise RuntimeError(f"Webcam {resolved} capture failed")
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
            return gray.astype(np.uint8), meta

        path = Path(resolved)
        if path.exists():
            # Prefer live device path, else still image
            if str(path).startswith("/dev/"):
                cap = cv2.VideoCapture(str(path))
                ok, frame = cap.read()
                cap.release()
                if not ok or frame is None:
                    raise RuntimeError(f"Device {path} capture failed")
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
                return gray.astype(np.uint8), meta

            frame = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if frame is None:
                raise RuntimeError(f"Could not read image: {path}")
            return frame.astype(np.uint8), meta

        raise RuntimeError(f"Camera source not found: {resolved}")


class GigECameraDriver(CameraDriver):
    """GigE Vision / GenICam capture (Harvesters+GenTL or Aravis)."""

    def capture(self, *, camera_id: str, recipe_id: str, source: str | None = None) -> tuple[np.ndarray, dict]:
        resolved = resolve_source(camera_id=camera_id, source=source)
        if not resolved:
            raise GigEUnavailableError(
                f"No GigE source for camera_id={camera_id!r}. "
                "Set CAMERA_SOURCE, CAMERA_SOURCES_JSON, or pass source= serial / user name / GenTL id."
            )
        image, meta = grab_gige_frame(resolved)
        meta.setdefault("driver", "gige")
        meta.setdefault("source", resolved)
        meta.setdefault("trigger_mode", "freerun")
        return image, meta


def get_camera_driver() -> CameraDriver:
    mode = os.getenv("CAMERA_DRIVER", "synthetic").strip().lower()
    if is_gige_driver(mode):
        return GigECameraDriver()
    if mode in {"opencv", "webcam", "file", "real"}:
        return OpenCvCameraDriver()
    return SyntheticCameraDriver()


def encode_image_b64(image: np.ndarray) -> str:
    import cv2

    ok, buf = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("PNG encode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")
