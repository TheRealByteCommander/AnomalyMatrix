"""Discover capture devices available to the edge-acquisition service."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

from gige_backend import discover_gige_devices, is_gige_driver


def _opencv_probe_index(index: int) -> bool:
    try:
        import cv2

        cap = cv2.VideoCapture(index)
        ok = bool(cap.isOpened())
        if ok:
            # Soft probe — some devices open but fail first read until streaming.
            _ret, _frame = cap.read()
        cap.release()
        return ok
    except Exception:
        return False


def _v4l2_devices() -> list[dict]:
    """Enumerate /dev/video* nodes (Linux)."""
    found: list[dict] = []
    video_nodes = sorted(Path("/dev").glob("video*"), key=lambda p: p.name)
    for path in video_nodes:
        # Prefer even indices for capture nodes when both metadata/capture exist;
        # still include all that OpenCV can open.
        index: int | None = None
        if path.name.startswith("video") and path.name[5:].isdigit():
            index = int(path.name[5:])
        label = path.name
        name_file = Path(f"/sys/class/video4linux/{path.name}/name")
        if name_file.exists():
            try:
                label = name_file.read_text(encoding="utf-8").strip() or path.name
            except OSError:
                pass

        available = False
        source = str(index) if index is not None else str(path)
        if index is not None:
            available = _opencv_probe_index(index)
        if not available and path.exists():
            # Path-based open as fallback
            try:
                import cv2

                cap = cv2.VideoCapture(str(path))
                available = bool(cap.isOpened())
                cap.release()
                source = str(path)
            except Exception:
                available = False

        camera_id = path.name  # e.g. video0
        found.append(
            {
                "camera_id": camera_id,
                "source": source,
                "path": str(path),
                "label": label,
                "driver": "opencv",
                "available": available,
                "index": index,
            }
        )
    # Only return nodes that actually open, unless none do (then return all for diagnostics)
    usable = [c for c in found if c["available"]]
    return usable if usable else found


def _synthetic_cameras(count: int = 4) -> list[dict]:
    cameras = []
    for i in range(1, count + 1):
        camera_id = f"cam-{i:02d}"
        cameras.append(
            {
                "camera_id": camera_id,
                "source": f"synthetic:{camera_id}",
                "path": None,
                "label": f"Synthetic Camera {i:02d}",
                "driver": "synthetic",
                "available": True,
                "index": i - 1,
            }
        )
    return cameras


def _driver_label() -> str:
    mode = os.getenv("CAMERA_DRIVER", "synthetic").strip().lower()
    if is_gige_driver(mode):
        return "gige"
    if mode in {"opencv", "webcam", "file", "real"}:
        return "opencv"
    return "synthetic"


def _mapped_cameras_from_env(*, gige_devices=None) -> list[dict]:
    """Optional explicit map: CAMERA_SOURCES_JSON='{"cam-a":"0","cam-b":"1"}'."""
    raw = os.getenv("CAMERA_SOURCES_JSON", "").strip()
    if not raw:
        return []
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(mapping, dict):
        return []
    driver = _driver_label()
    devices = gige_devices
    if driver == "gige" and devices is None:
        devices, _info = discover_gige_devices()
    cameras = []
    for camera_id, source in mapping.items():
        source_s = str(source).strip()
        available = True
        extra: dict = {}
        if driver == "gige":
            from gige_backend import match_gige_device

            match = match_gige_device(devices or [], source_s)
            available = match is not None and match.available
            if match:
                extra = {
                    "model": match.model,
                    "serial": match.serial,
                    "ip": match.ip,
                    "interface": match.interface,
                    "user_id": match.user_id,
                    "gentl_id": match.gentl_id,
                    "backend": match.backend,
                    "label": match.label,
                }
        elif source_s.isdigit():
            available = _opencv_probe_index(int(source_s))
        elif source_s.startswith("/dev/"):
            available = Path(source_s).exists()
        cameras.append(
            {
                "camera_id": str(camera_id),
                "source": source_s,
                "path": source_s if source_s.startswith("/") else None,
                "label": extra.get("label") or str(camera_id),
                "driver": driver,
                "available": available,
                "index": int(source_s) if source_s.isdigit() else None,
                **extra,
            }
        )
    return cameras


def discover_cameras() -> dict:
    """Return discovered cameras for the active driver."""
    mode = os.getenv("CAMERA_DRIVER", "synthetic").strip().lower()
    driver = _driver_label()
    gige_devices = None
    gige_info: dict = {}
    if driver == "gige":
        gige_devices, gige_info = discover_gige_devices()
    mapped = _mapped_cameras_from_env(gige_devices=gige_devices)
    payload = {
        "driver": driver,
        "host": platform.node(),
        "max_selectable": 4,
        "min_selectable": 1,
    }
    if mapped:
        payload["cameras"] = mapped
        if driver == "gige":
            payload["backend"] = gige_info.get("backend")
            payload["gentl_producers"] = gige_info.get("cti_files") or []
            if gige_info.get("error"):
                payload["error"] = gige_info["error"]
        return payload

    if driver == "gige":
        cameras = [d.to_dict() for d in (gige_devices or [])]
        payload.update(
            {
                "cameras": cameras,
                "backend": gige_info.get("backend"),
                "gentl_producers": gige_info.get("cti_files") or [],
            }
        )
        if gige_info.get("error"):
            payload["error"] = gige_info["error"]
        elif not cameras:
            payload["warning"] = (
                "No GigE Vision devices found. Check host networking, NIC subnet, "
                "Jumbo frames, and that the camera answers GVCP (UDP 3956)."
            )
        return payload

    if mode in {"opencv", "webcam", "file", "real"}:
        cameras = _v4l2_devices()
        # Also probe common indices 0..3 if /dev scan empty (macOS / containers)
        if not cameras:
            for idx in range(4):
                if _opencv_probe_index(idx):
                    cameras.append(
                        {
                            "camera_id": f"video{idx}",
                            "source": str(idx),
                            "path": f"/dev/video{idx}",
                            "label": f"Camera {idx}",
                            "driver": "opencv",
                            "available": True,
                            "index": idx,
                        }
                    )
        payload.update({"driver": "opencv", "cameras": cameras})
        return payload

    payload.update({"driver": "synthetic", "cameras": _synthetic_cameras(4)})
    return payload


def resolve_source(*, camera_id: str, source: str | None = None) -> str | None:
    """Resolve capture source for a camera_id."""
    if source:
        return source.strip()
    mapped = _mapped_cameras_from_env()
    for cam in mapped:
        if cam["camera_id"] == camera_id:
            return str(cam["source"])
    # camera_id may itself be an index or path
    if camera_id.isdigit() or camera_id.startswith("/dev/") or camera_id.startswith("synthetic:"):
        return camera_id
    # videoN → index N
    if camera_id.startswith("video") and camera_id[5:].isdigit():
        return camera_id[5:]
    if is_gige_driver():
        # serial, user-defined name, or GenTL id used as camera_id
        return camera_id.strip() or os.getenv("CAMERA_SOURCE", "").strip() or None
    return os.getenv("CAMERA_SOURCE", "").strip() or None
