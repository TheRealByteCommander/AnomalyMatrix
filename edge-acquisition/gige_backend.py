"""GigE Vision / GenICam capture backends for edge-acquisition.

Architecture
------------
Two backends share one interface so hardware-trigger / encoder sync can be
added later without changing the HTTP or driver API:

* **Harvesters** — portable GenICam via a GenTL producer (``.cti``).
  Preferred when ``GENICAM_GENTL64_PATH`` / ``GIGE_GENTL_CTI`` points at a
  producer (Basler pylon, MATRIX VISION, IDS peak, …).
* **Aravis** — open GigE Vision stack (``gir1.2-aravis``). Used when no
  producer is mounted; talks GVCP/GVSP directly, no vendor SDK.

``GIGE_BACKEND=auto|harvesters|aravis`` selects the path (default: auto).

MVP capture is one software-trigger or free-run frame per call. Hardware
line/encoder trigger is stubbed via the same GenICam nodes
(``TriggerMode`` / ``TriggerSource``) and documented as follow-up.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

GIGE_DRIVER_ALIASES = frozenset({"gige", "genicam", "gigevision", "gev"})

DEFAULT_GENTL_DIR = Path("/opt/gentl")

_LOCK = threading.Lock()


class GigEUnavailableError(RuntimeError):
    """Raised when no GenTL producer / Aravis runtime is usable."""


@dataclass
class GigEDevice:
    camera_id: str
    source: str
    label: str
    driver: str = "gige"
    available: bool = True
    index: int | None = None
    path: str | None = None
    model: str | None = None
    serial: str | None = None
    ip: str | None = None
    interface: str | None = None
    user_id: str | None = None
    vendor: str | None = None
    gentl_id: str | None = None
    backend: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def is_gige_driver(mode: str | None = None) -> bool:
    value = (mode if mode is not None else os.getenv("CAMERA_DRIVER", "")).strip().lower()
    value = value.replace("_", "").replace("-", "").replace(" ", "")
    if value == "gige":
        return True
    return value in GIGE_DRIVER_ALIASES


def _env_float(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        logger.warning("Ignoring invalid float for %s=%r", name, raw)
        return None


def _env_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Ignoring invalid int for %s=%r", name, raw)
        return None


def trigger_mode_from_env() -> str:
    raw = os.getenv("CAMERA_TRIGGER", "freerun").strip().lower()
    if raw in {"software", "sw", "soft"}:
        return "software"
    if raw in {"hardware", "hw", "line", "encoder"}:
        return "hardware"
    return "freerun"


def exposure_ms_from_env() -> float | None:
    ms = _env_float("CAMERA_EXPOSURE_MS")
    if ms is not None:
        return ms
    us = _env_float("CAMERA_EXPOSURE_US")
    if us is not None:
        return us / 1000.0
    return None


def gain_db_from_env() -> float | None:
    return _env_float("CAMERA_GAIN_DB")


def _sanitize_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip("-") or "gige"
    return cleaned[:80]


def _pick_camera_id(*, user_id: str | None, serial: str | None, gentl_id: str | None, index: int) -> str:
    for candidate in (user_id, serial, gentl_id):
        if candidate and str(candidate).strip():
            return _sanitize_id(str(candidate))
    return f"gige-{index}"


def find_cti_files() -> list[Path]:
    """Locate GenTL producer libraries (``.cti``)."""
    found: list[Path] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        key = str(resolved)
        if key in seen:
            return
        if path.is_file() and path.suffix.lower() == ".cti":
            seen.add(key)
            found.append(path)

    def _scan_dir(directory: Path) -> None:
        if not directory.is_dir():
            return
        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() == ".cti":
                    _add(item)
                elif item.is_dir():
                    # One extra level (vendor layouts like /opt/pylon/lib/gentlproducer/)
                    try:
                        for nested in item.iterdir():
                            if nested.is_file() and nested.suffix.lower() == ".cti":
                                _add(nested)
                    except OSError:
                        continue
        except OSError:
            return

    explicit = os.getenv("GIGE_GENTL_CTI", "").strip()
    if explicit:
        p = Path(explicit)
        if p.is_file():
            _add(p)
        else:
            _scan_dir(p)

    for part in os.getenv("GENICAM_GENTL64_PATH", "").split(os.pathsep):
        part = part.strip()
        if not part:
            continue
        p = Path(part)
        if p.is_file():
            _add(p)
        else:
            _scan_dir(p)

    _scan_dir(DEFAULT_GENTL_DIR)
    return found


def _producer_hint() -> str:
    return (
        "Install a GenTL producer and set GENICAM_GENTL64_PATH or GIGE_GENTL_CTI "
        "to the directory/file containing the .cti (Harvesters path), or install "
        "Aravis (libaravis + gir1.2-aravis) for the open GigE Vision stack. "
        "See edge-acquisition/README.md and docs/CONFIGURATION.md."
    )


def to_grayscale(image: np.ndarray, pixel_format: str | None = None) -> np.ndarray:
    """Convert Bayer / RGB / Mono buffers to uint8 grayscale."""
    import cv2

    if image is None or image.size == 0:
        raise RuntimeError("GigE capture returned an empty frame")

    fmt = (pixel_format or "").replace(" ", "").replace("_", "").replace("-", "").upper()
    arr = np.ascontiguousarray(image)

    if arr.ndim == 3 and arr.shape[2] >= 3:
        # Assume RGB unless the format name says BGR.
        if "BGR" in fmt:
            gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_BGR2GRAY)
        else:
            gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
        return gray.astype(np.uint8)

    if arr.ndim != 2:
        raise RuntimeError(f"Unsupported GigE frame shape {arr.shape} (format={pixel_format!r})")

    if arr.dtype == np.uint16:
        arr = (arr / 257).astype(np.uint8)
    elif arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)

    bayer_codes = {
        "BAYERRG8": cv2.COLOR_BAYER_RG2GRAY,
        "BAYERRG": cv2.COLOR_BAYER_RG2GRAY,
        "RG8": cv2.COLOR_BAYER_RG2GRAY,
        "BAYERGR8": cv2.COLOR_BAYER_GR2GRAY,
        "BAYERGR": cv2.COLOR_BAYER_GR2GRAY,
        "GR8": cv2.COLOR_BAYER_GR2GRAY,
        "BAYERGB8": cv2.COLOR_BAYER_GB2GRAY,
        "BAYERGB": cv2.COLOR_BAYER_GB2GRAY,
        "GB8": cv2.COLOR_BAYER_GB2GRAY,
        "BAYERBG8": cv2.COLOR_BAYER_BG2GRAY,
        "BAYERBG": cv2.COLOR_BAYER_BG2GRAY,
        "BG8": cv2.COLOR_BAYER_BG2GRAY,
    }
    if "BAYER" in fmt or fmt in bayer_codes:
        code = None
        for key, cv_code in bayer_codes.items():
            if key in fmt or fmt == key:
                code = cv_code
                break
        if code is None:
            code = cv2.COLOR_BAYER_RG2GRAY
        try:
            return cv2.cvtColor(arr, code)
        except cv2.error as exc:
            raise RuntimeError(f"Bayer→gray conversion failed for {pixel_format!r}") from exc

    return arr.astype(np.uint8)


def match_gige_device(devices: list[GigEDevice], source: str) -> GigEDevice | None:
    needle = source.strip()
    if not needle:
        return None
    lowered = needle.lower()
    prefixes = ("serial:", "id:", "user:", "ip:", "gentl:", "name:")
    field = None
    value = needle
    for prefix in prefixes:
        if lowered.startswith(prefix):
            field = prefix[:-1]
            value = needle[len(prefix) :].strip()
            break

    def _eq(candidate: str | None) -> bool:
        return bool(candidate) and str(candidate).strip().lower() == value.lower()

    for dev in devices:
        if field == "serial" and _eq(dev.serial):
            return dev
        if field in {"id", "gentl"} and (_eq(dev.gentl_id) or _eq(dev.source) or _eq(dev.camera_id)):
            return dev
        if field == "user" and (_eq(dev.user_id) or _eq(dev.camera_id)):
            return dev
        if field == "ip" and _eq(dev.ip):
            return dev
        if field == "name" and (_eq(dev.label) or _eq(dev.model) or _eq(dev.user_id)):
            return dev
        if any(
            _eq(x)
            for x in (
                dev.camera_id,
                dev.source,
                dev.serial,
                dev.gentl_id,
                dev.user_id,
                dev.ip,
                dev.label,
            )
        ):
            return dev
    return None


def _safe_attr(obj: Any, *names: str) -> str | None:
    for name in names:
        try:
            value = obj[name] if isinstance(obj, dict) else getattr(obj, name)
        except Exception:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"none", "n/a"}:
            return text
    return None


def _try_node_set(node_map: Any, names: tuple[str, ...], value: Any) -> bool:
    for name in names:
        node = None
        try:
            node = getattr(node_map, name)
        except Exception:
            try:
                node = node_map.get_node(name)
            except Exception:
                continue
        if node is None:
            continue
        try:
            if hasattr(node, "value"):
                node.value = value
            elif hasattr(node, "set_value"):
                node.set_value(value)
            else:
                continue
            return True
        except Exception:
            logger.debug("Could not set GenICam node %s", name, exc_info=True)
    return False


def _try_node_get(node_map: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        node = None
        try:
            node = getattr(node_map, name)
        except Exception:
            try:
                node = node_map.get_node(name)
            except Exception:
                continue
        if node is None:
            continue
        try:
            if hasattr(node, "value"):
                return node.value
            if hasattr(node, "to_string"):
                return node.to_string()
        except Exception:
            continue
    return None


def _try_node_execute(node_map: Any, names: tuple[str, ...]) -> bool:
    for name in names:
        node = None
        try:
            node = getattr(node_map, name)
        except Exception:
            try:
                node = node_map.get_node(name)
            except Exception:
                continue
        if node is None:
            continue
        try:
            if hasattr(node, "execute"):
                node.execute()
                return True
            if callable(node):
                node()
                return True
        except Exception:
            logger.debug("Could not execute GenICam command %s", name, exc_info=True)
    return False


class GigEBackend(ABC):
    name: str = "gige"

    @abstractmethod
    def discover(self) -> list[GigEDevice]:
        raise NotImplementedError

    @abstractmethod
    def grab(self, source: str) -> tuple[np.ndarray, dict]:
        raise NotImplementedError


class HarvestersBackend(GigEBackend):
    name = "harvesters"

    def __init__(self, cti_files: list[Path] | None = None):
        self.cti_files = cti_files if cti_files is not None else find_cti_files()
        if not self.cti_files:
            raise GigEUnavailableError(
                "No GenTL producer (.cti) found. " + _producer_hint()
            )
        try:
            from harvesters.core import Harvester  # noqa: F401
        except Exception as exc:
            raise GigEUnavailableError(
                "Python package 'harvesters' is not importable. "
                "pip install harvesters (pulls genicam). " + _producer_hint()
            ) from exc

    def _harvester(self):
        from harvesters.core import Harvester

        h = Harvester()
        loaded = 0
        errors: list[str] = []
        for cti in self.cti_files:
            try:
                h.add_file(str(cti))
                loaded += 1
            except Exception as exc:
                errors.append(f"{cti}: {exc}")
        if loaded == 0:
            h.reset()
            raise GigEUnavailableError(
                "Failed to load GenTL producer(s): "
                + ("; ".join(errors) or "unknown error")
                + ". "
                + _producer_hint()
            )
        try:
            h.update()
        except Exception as exc:
            h.reset()
            raise GigEUnavailableError(f"GenTL producer update failed: {exc}") from exc
        return h

    def _devices_from_harvester(self, h) -> list[GigEDevice]:
        devices: list[GigEDevice] = []
        infos = list(getattr(h, "device_info_list", []) or [])
        for idx, info in enumerate(infos):
            gentl_id = _safe_attr(info, "id_", "id")
            serial = _safe_attr(info, "serial_number", "serial")
            user_id = _safe_attr(info, "user_defined_name", "user_id")
            model = _safe_attr(info, "model", "model_name")
            vendor = _safe_attr(info, "vendor")
            display = _safe_attr(info, "display_name") or model or gentl_id or f"GigE-{idx}"
            ip = _safe_attr(info, "ip", "ip_address")
            interface = _safe_attr(info, "tl_type", "interface")
            camera_id = _pick_camera_id(user_id=user_id, serial=serial, gentl_id=gentl_id, index=idx)
            source = gentl_id or serial or camera_id
            devices.append(
                GigEDevice(
                    camera_id=camera_id,
                    source=source,
                    label=display,
                    available=True,
                    index=idx,
                    model=model,
                    serial=serial,
                    ip=ip,
                    interface=interface,
                    user_id=user_id,
                    vendor=vendor,
                    gentl_id=gentl_id,
                    backend=self.name,
                )
            )
        return devices

    def discover(self) -> list[GigEDevice]:
        h = self._harvester()
        try:
            return self._devices_from_harvester(h)
        finally:
            try:
                h.reset()
            except Exception:
                pass

    def grab(self, source: str) -> tuple[np.ndarray, dict]:
        h = self._harvester()
        ia = None
        try:
            devices = self._devices_from_harvester(h)
            if not devices:
                raise RuntimeError("No GigE/GenICam devices reported by the GenTL producer")
            target = match_gige_device(devices, source) or devices[0]
            spec: dict[str, str] = {}
            if target.serial:
                spec["serial_number"] = target.serial
            elif target.gentl_id:
                spec["id_"] = target.gentl_id
            elif target.user_id:
                spec["user_defined_name"] = target.user_id
            try:
                ia = h.create(spec) if spec else h.create(target.index or 0)
            except Exception:
                ia = h.create(target.index or 0)

            node_map = getattr(getattr(ia, "remote_device", None), "node_map", None)
            applied_trigger = trigger_mode_from_env()
            exposure_ms = exposure_ms_from_env()
            gain_db = gain_db_from_env()
            packet = _env_int("GIGE_PACKET_SIZE")

            if node_map is not None:
                if packet:
                    _try_node_set(node_map, ("GevSCPSPacketSize", "GevStreamChannelPacketSize"), packet)
                if exposure_ms is not None:
                    _try_node_set(node_map, ("ExposureTime", "ExposureTimeAbs"), exposure_ms * 1000.0)
                    _try_node_set(node_map, ("ExposureTimeMs",), exposure_ms)
                if gain_db is not None:
                    _try_node_set(node_map, ("Gain", "GainRaw", "GainAbs"), gain_db)
                _apply_trigger_nodes(node_map, applied_trigger)

            timeout_s = _env_float("CAMERA_GRAB_TIMEOUT_S") or 5.0
            ia.start()
            try:
                if applied_trigger == "software" and node_map is not None:
                    _try_node_execute(node_map, ("TriggerSoftware", "SoftwareTrigger"))
                buffer = ia.fetch(timeout=timeout_s)
            except Exception as exc:
                raise RuntimeError(f"GigE grab failed for source {source!r}: {exc}") from exc

            try:
                component = buffer.payload.components[0]
                height = int(component.height)
                width = int(component.width)
                raw = np.copy(component.data)
                pixel_format = str(
                    getattr(component, "data_format", None)
                    or getattr(component, "pixel_format", None)
                    or ""
                )
                if raw.ndim == 1 and height > 0 and width > 0:
                    channels = int(raw.size / (height * width)) if height * width else 1
                    if channels <= 1:
                        raw = raw.reshape(height, width)
                    else:
                        raw = raw.reshape(height, width, channels)
                gray = to_grayscale(raw, pixel_format)
            finally:
                try:
                    buffer.queue()
                except Exception:
                    try:
                        buffer.release()
                    except Exception:
                        pass

            if node_map is not None:
                if exposure_ms is None:
                    exp_val = _try_node_get(node_map, ("ExposureTime", "ExposureTimeAbs"))
                    if isinstance(exp_val, (int, float)):
                        exposure_ms = float(exp_val) / 1000.0
                if gain_db is None:
                    gain_val = _try_node_get(node_map, ("Gain", "GainAbs"))
                    if isinstance(gain_val, (int, float)):
                        gain_db = float(gain_val)

            meta = {
                "driver": "gige",
                "backend": self.name,
                "source": target.source,
                "exposure_ms": float(exposure_ms if exposure_ms is not None else 10.0),
                "gain_db": float(gain_db if gain_db is not None else 0.0),
                "trigger_mode": applied_trigger,
                "model": target.model,
                "serial": target.serial,
                "pixel_format": pixel_format,
            }
            return gray, meta
        finally:
            if ia is not None:
                try:
                    ia.stop()
                except Exception:
                    pass
                try:
                    ia.destroy()
                except Exception:
                    pass
            try:
                h.reset()
            except Exception:
                pass


def _apply_trigger_nodes(node_map: Any, mode: str) -> None:
    if mode == "freerun":
        _try_node_set(node_map, ("TriggerMode",), "Off")
        _try_node_set(node_map, ("AcquisitionMode",), "Continuous")
        return
    _try_node_set(node_map, ("AcquisitionMode",), "Continuous")
    _try_node_set(node_map, ("TriggerMode",), "On")
    if mode == "software":
        _try_node_set(node_map, ("TriggerSource",), "Software")
        return
    # hardware / encoder — best-effort; full line-sync is a follow-up
    source = os.getenv("CAMERA_TRIGGER_SOURCE", "Line1").strip() or "Line1"
    _try_node_set(node_map, ("TriggerSource",), source)
    _try_node_set(node_map, ("TriggerActivation",), os.getenv("CAMERA_TRIGGER_ACTIVATION", "RisingEdge"))


class AravisBackend(GigEBackend):
    name = "aravis"

    def __init__(self):
        try:
            import gi

            gi.require_version("Aravis", "0.8")
            from gi.repository import Aravis  # noqa: F401
        except Exception as exc:
            raise GigEUnavailableError(
                "Aravis GigE Vision runtime is not importable (PyGObject / gir1.2-aravis). "
                + _producer_hint()
            ) from exc

    def _aravis(self):
        from gi.repository import Aravis

        return Aravis

    def discover(self) -> list[GigEDevice]:
        Aravis = self._aravis()
        Aravis.update_device_list()
        n = int(Aravis.get_n_devices())
        devices: list[GigEDevice] = []
        for idx in range(n):
            gentl_id = _call_str(Aravis.get_device_id, idx)
            serial = _call_str(getattr(Aravis, "get_device_serial_nbr", None), idx)
            model = _call_str(getattr(Aravis, "get_device_model", None), idx)
            vendor = _call_str(getattr(Aravis, "get_device_vendor", None), idx)
            ip = _call_str(getattr(Aravis, "get_device_address", None), idx)
            interface = _call_str(getattr(Aravis, "get_device_protocol", None), idx)
            user_id = None
            try:
                cam = Aravis.Camera.new(gentl_id)
                user_id = _call_str(getattr(cam, "get_device_id", None))
                if hasattr(cam, "get_string"):
                    try:
                        user_id = cam.get_string("DeviceUserID") or user_id
                    except Exception:
                        pass
            except Exception:
                cam = None
            camera_id = _pick_camera_id(user_id=user_id, serial=serial, gentl_id=gentl_id, index=idx)
            label_parts = [p for p in (vendor, model) if p]
            label = " ".join(label_parts) if label_parts else (gentl_id or camera_id)
            if serial:
                label = f"{label} ({serial})"
            devices.append(
                GigEDevice(
                    camera_id=camera_id,
                    source=gentl_id or serial or camera_id,
                    label=label,
                    available=True,
                    index=idx,
                    model=model,
                    serial=serial,
                    ip=ip,
                    interface=interface,
                    user_id=user_id,
                    vendor=vendor,
                    gentl_id=gentl_id,
                    backend=self.name,
                )
            )
        return devices

    def grab(self, source: str) -> tuple[np.ndarray, dict]:
        Aravis = self._aravis()
        devices = self.discover()
        target = match_gige_device(devices, source)
        device_id = (target.gentl_id if target else None) or source
        try:
            camera = Aravis.Camera.new(device_id if device_id else None)
        except Exception as exc:
            raise RuntimeError(f"Could not open GigE camera {source!r}: {exc}") from exc
        if camera is None:
            raise RuntimeError(f"Could not open GigE camera {source!r}")

        applied_trigger = trigger_mode_from_env()
        exposure_ms = exposure_ms_from_env()
        gain_db = gain_db_from_env()
        packet = _env_int("GIGE_PACKET_SIZE")

        try:
            if hasattr(camera, "gv_auto_packet_size"):
                try:
                    camera.gv_auto_packet_size()
                except Exception:
                    pass
            if packet and hasattr(camera, "gv_set_packet_size"):
                try:
                    camera.gv_set_packet_size(packet)
                except Exception:
                    pass
            if exposure_ms is not None:
                _aravis_set_exposure(camera, exposure_ms)
            if gain_db is not None and hasattr(camera, "set_gain"):
                try:
                    camera.set_gain(gain_db)
                except Exception:
                    pass
            _aravis_apply_trigger(camera, applied_trigger)
        except GigEUnavailableError:
            raise
        except Exception:
            logger.debug("Optional GigE feature setup failed", exc_info=True)

        timeout_us = int((_env_float("CAMERA_GRAB_TIMEOUT_S") or 5.0) * 1_000_000)
        payload = int(camera.get_payload())
        stream = camera.create_stream(None, None)
        if stream is None:
            raise RuntimeError("Aravis could not create a stream (check NIC / Jumbo frames / host network)")
        try:
            for _ in range(4):
                stream.push_buffer(Aravis.Buffer.new_allocate(payload))
            camera.start_acquisition()
            if applied_trigger == "software":
                _aravis_software_trigger(camera)
            buf = stream.timeout_pop_buffer(timeout_us)
            if buf is None:
                raise RuntimeError(
                    f"GigE grab timeout after {timeout_us / 1e6:.1f}s for {source!r} "
                    "(trigger? network? Jumbo frames?)"
                )
            try:
                status = buf.get_status()
                success = getattr(getattr(Aravis, "BufferStatus", None), "SUCCESS", 0)
                if status not in {success, 0}:
                    raise RuntimeError(f"GigE buffer status {status} for {source!r}")
                data = bytes(buf.get_data())
                width = int(buf.get_image_width())
                height = int(buf.get_image_height())
                pixel_enum = buf.get_image_pixel_format()
                pixel_format = _aravis_pixel_name(Aravis, pixel_enum)
                raw = _aravis_reshape(data, width, height, pixel_format)
                gray = to_grayscale(raw, pixel_format)
            finally:
                try:
                    stream.push_buffer(buf)
                except Exception:
                    pass
        finally:
            try:
                camera.stop_acquisition()
            except Exception:
                pass

        if exposure_ms is None and hasattr(camera, "get_exposure_time"):
            try:
                exposure_ms = float(camera.get_exposure_time()) / 1000.0
            except Exception:
                pass
        if gain_db is None and hasattr(camera, "get_gain"):
            try:
                gain_db = float(camera.get_gain())
            except Exception:
                pass

        meta = {
            "driver": "gige",
            "backend": self.name,
            "source": device_id,
            "exposure_ms": float(exposure_ms if exposure_ms is not None else 10.0),
            "gain_db": float(gain_db if gain_db is not None else 0.0),
            "trigger_mode": applied_trigger,
            "model": target.model if target else None,
            "serial": target.serial if target else None,
            "pixel_format": pixel_format,
        }
        return gray, meta


def _call_str(fn, *args) -> str | None:
    if fn is None:
        return None
    try:
        value = fn(*args) if args else fn()
    except Exception:
        return None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _aravis_set_exposure(camera: Any, exposure_ms: float) -> None:
    us = exposure_ms * 1000.0
    for name, value in (("set_exposure_time", us), ("set_exposure_time_us", us)):
        fn = getattr(camera, name, None)
        if callable(fn):
            try:
                fn(value)
                return
            except Exception:
                continue
    device = getattr(camera, "get_device", lambda: None)()
    if device is not None:
        try:
            device.set_float_feature_value("ExposureTime", us)
        except Exception:
            pass


def _aravis_apply_trigger(camera: Any, mode: str) -> None:
    device = getattr(camera, "get_device", lambda: None)()
    if device is None:
        return

    def _set(name: str, value: str) -> None:
        try:
            device.set_string_feature_value(name, value)
        except Exception:
            pass

    if mode == "freerun":
        _set("TriggerMode", "Off")
        return
    _set("TriggerMode", "On")
    if mode == "software":
        _set("TriggerSource", "Software")
        return
    _set("TriggerSource", os.getenv("CAMERA_TRIGGER_SOURCE", "Line1").strip() or "Line1")


def _aravis_software_trigger(camera: Any) -> None:
    if hasattr(camera, "software_trigger"):
        try:
            camera.software_trigger()
            return
        except Exception:
            pass
    device = getattr(camera, "get_device", lambda: None)()
    if device is not None:
        try:
            device.execute_command("TriggerSoftware")
        except Exception:
            pass


def _aravis_pixel_name(Aravis: Any, pixel_enum: Any) -> str:
    fn = getattr(Aravis, "pixel_format_to_string", None)
    if callable(fn):
        try:
            name = fn(pixel_enum)
            if name:
                return str(name)
        except Exception:
            pass
    return str(pixel_enum)


def _aravis_reshape(data: bytes, width: int, height: int, pixel_format: str) -> np.ndarray:
    if width <= 0 or height <= 0:
        raise RuntimeError("GigE buffer has invalid width/height")
    fmt = (pixel_format or "").replace(" ", "").replace("_", "").upper()
    buf = np.frombuffer(data, dtype=np.uint8)
    if "16" in fmt or "MONO12" in fmt:
        # Prefer native 16-bit view when the payload size matches.
        if buf.size >= width * height * 2:
            arr16 = np.frombuffer(data, dtype=np.uint16, count=width * height)
            return arr16.reshape(height, width)
    pixels = width * height
    if buf.size >= pixels * 3 and any(x in fmt for x in ("RGB", "BGR", "YUV444")):
        return buf[: pixels * 3].reshape(height, width, 3)
    if buf.size >= pixels:
        return buf[:pixels].reshape(height, width)
    raise RuntimeError(
        f"GigE payload too small ({buf.size} bytes) for {width}x{height} {pixel_format}"
    )


def _requested_backend() -> str:
    return os.getenv("GIGE_BACKEND", "auto").strip().lower() or "auto"


def backend_status() -> dict:
    """Diagnostic snapshot (no camera I/O besides optional Aravis import)."""
    cti = [str(p) for p in find_cti_files()]
    harvesters_ok = False
    harvesters_error = None
    try:
        from harvesters.core import Harvester  # noqa: F401

        harvesters_ok = True
    except Exception as exc:
        harvesters_error = str(exc)

    aravis_ok = False
    aravis_error = None
    try:
        import gi

        gi.require_version("Aravis", "0.8")
        from gi.repository import Aravis  # noqa: F401

        aravis_ok = True
    except Exception as exc:
        aravis_error = str(exc)

    return {
        "requested": _requested_backend(),
        "cti_files": cti,
        "harvesters": harvesters_ok,
        "harvesters_error": harvesters_error,
        "aravis": aravis_ok,
        "aravis_error": aravis_error,
    }


def select_backend() -> GigEBackend:
    requested = _requested_backend()
    cti_files = find_cti_files()
    errors: list[str] = []

    def _harvesters() -> HarvestersBackend:
        return HarvestersBackend(cti_files=cti_files)

    def _aravis() -> AravisBackend:
        return AravisBackend()

    if requested in {"harvesters", "gentl", "genicam"}:
        return _harvesters()
    if requested in {"aravis", "arv"}:
        return _aravis()

    # auto: prefer GenTL when a producer is present, else Aravis.
    if cti_files:
        try:
            return _harvesters()
        except GigEUnavailableError as exc:
            errors.append(str(exc))
    try:
        return _aravis()
    except GigEUnavailableError as extra:
        errors.append(str(extra))
    raise GigEUnavailableError("GigE/GenICam backend unavailable. " + " ".join(errors) + " " + _producer_hint())


def discover_gige_devices() -> tuple[list[GigEDevice], dict]:
    """Return devices plus backend diagnostics. Never raises for missing producer."""
    info = backend_status()
    try:
        with _LOCK:
            backend = select_backend()
            devices = backend.discover()
        info["backend"] = backend.name
        return devices, info
    except GigEUnavailableError as exc:
        info["error"] = str(exc)
        info["backend"] = None
        return [], info
    except Exception as exc:
        logger.exception("GigE discovery failed")
        info["error"] = f"GigE discovery failed: {exc}"
        info["backend"] = info.get("backend")
        return [], info


def grab_gige_frame(source: str) -> tuple[np.ndarray, dict]:
    if not (source or "").strip():
        raise RuntimeError("GigE capture requires CAMERA_SOURCE or a resolved camera id/serial")
    with _LOCK:
        backend = select_backend()
        return backend.grab(source.strip())
