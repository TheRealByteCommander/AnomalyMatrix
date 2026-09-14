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


_OPENCV_DEFAULT_FOURCC = "MJPG"
_OPENCV_DEFAULT_WIDTH = 3840
_OPENCV_DEFAULT_HEIGHT = 2160
_OPENCV_DEFAULT_FPS = 30.0
_FOURCC_ALIASES = {
    "MJPEG": "MJPG",
    "JPEG": "MJPG",
}


def _env_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _env_positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = float(str(raw).strip())
    except ValueError:
        return default
    return value if value > 0 else default


def opencv_capture_mode_from_env() -> dict:
    """USB/V4L2 capture mode. Ignored by GigE and synthetic drivers."""
    raw = os.getenv("CAMERA_FOURCC", _OPENCV_DEFAULT_FOURCC)
    fourcc = str(raw).strip().upper() if raw is not None else _OPENCV_DEFAULT_FOURCC
    fourcc = _FOURCC_ALIASES.get(fourcc, fourcc) or _OPENCV_DEFAULT_FOURCC
    fourcc = (fourcc + "    ")[:4]
    return {
        "fourcc": fourcc,
        "width": _env_positive_int("CAMERA_WIDTH", _OPENCV_DEFAULT_WIDTH),
        "height": _env_positive_int("CAMERA_HEIGHT", _OPENCV_DEFAULT_HEIGHT),
        "fps": _env_positive_float("CAMERA_FPS", _OPENCV_DEFAULT_FPS),
    }


def _fourcc_code(cv2, fourcc: str) -> int:
    return int(cv2.VideoWriter_fourcc(*fourcc))


def _fourcc_name(code: float | int) -> str:
    value = int(code)
    if value <= 0:
        return ""
    chars: list[str] = []
    for shift in range(4):
        ch = (value >> (8 * shift)) & 0xFF
        chars.append(chr(ch) if 32 <= ch < 127 else "?")
    return "".join(chars).rstrip()


def _configure_opencv_capture(cv2, cap, requested: dict | None = None) -> dict:
    """Set FOURCC then geometry/fps before the first read (UVC 4K needs MJPG)."""
    requested = requested or opencv_capture_mode_from_env()
    cap.set(cv2.CAP_PROP_FOURCC, _fourcc_code(cv2, requested["fourcc"]))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(requested["width"]))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(requested["height"]))
    cap.set(cv2.CAP_PROP_FPS, float(requested["fps"]))
    return requested


def _opencv_negotiated_mode(cv2, cap, frame, requested: dict) -> dict:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    fourcc = _fourcc_name(cap.get(cv2.CAP_PROP_FOURCC) or 0)
    if width <= 0 and frame is not None and getattr(frame, "ndim", 0) >= 2:
        width = int(frame.shape[1])
    if height <= 0 and frame is not None and getattr(frame, "ndim", 0) >= 2:
        height = int(frame.shape[0])
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "fourcc": fourcc or requested["fourcc"],
    }


def _grab_live_opencv(cv2, device: int | str, *, error_label: str) -> tuple[np.ndarray, dict]:
    cap = cv2.VideoCapture(device)
    try:
        requested = _configure_opencv_capture(cv2, cap)
        ok, frame = cap.read()
        negotiated = _opencv_negotiated_mode(cv2, cap, frame, requested)
    finally:
        cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"{error_label} capture failed")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    return gray.astype(np.uint8), negotiated


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
            gray, negotiated = _grab_live_opencv(
                cv2, int(resolved), error_label=f"Webcam {resolved}"
            )
            meta.update(negotiated)
            return gray, meta

        path = Path(resolved)
        if path.exists():
            # Prefer live device path, else still image
            if str(path).startswith("/dev/"):
                gray, negotiated = _grab_live_opencv(
                    cv2, str(path), error_label=f"Device {path}"
                )
                meta.update(negotiated)
                return gray, meta

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
