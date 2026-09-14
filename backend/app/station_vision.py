"""EOL station vision profile (cameras, lighting, perspectives, export)."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .camera_limits import HARD_CAP, MIN_CAMERAS, max_cameras
from .storage_layout import station_id as default_station_id
from .yaml_util import dumps as yaml_dumps
from .yaml_util import loads as yaml_loads

CAMERA_ROLES = ("top", "side", "bottom", "stf", "completeness", "other")
TRIGGER_MODES = ("freerun", "software", "hardware", "mqtt", "opcua")
COLOR_MODES = ("mono", "rgb", "bayer")
IMAGE_FORMATS = ("png", "jpeg", "raw")
CHECKLIST_ITEMS = (
    "corners_visible",
    "edges_visible",
    "features_visible",
    "bottom_view_covered",
    "lighting_uniform",
    "no_motion_blur",
    "focus_confirmed",
    "fov_covers_part",
)


class StationVisionError(ValueError):
    pass


def _default_camera_slot(index: int, camera_id: str | None = None) -> dict:
    roles = ["top", "side", "bottom", "stf"]
    return {
        "slot": index,
        "camera_id": camera_id or f"cam-{index:02d}",
        "role": roles[index - 1] if index <= len(roles) else "other",
        "enabled": True,
        "lens_notes": "",
        "fov_notes": "",
        "working_distance_mm": None,
        "lighting": {
            "profile_name": "default",
            "exposure_ms": 8.0,
            "gain_db": 0.0,
            "trigger_mode": "software",
            "light_controller": {
                "enabled": False,
                "protocol": "config",
                "endpoint": "",
                "channel": None,
                "notes": "Optional strobe/controller hook (MQTT/OPC-UA/HTTP).",
            },
        },
        "capture": {
            "image_format": "png",
            "jpeg_quality": 92,
            "width": None,
            "height": None,
            "color_mode": "mono",
            "pixel_format": "",
        },
    }


def default_profile() -> dict:
    n = max(MIN_CAMERAS, min(max_cameras(), 4))
    cameras = [_default_camera_slot(i) for i in range(1, n + 1)]
    cameras[0]["role"] = "top"
    return {
        "schema": "StationVisionProfile",
        "schema_version": "1.0.0",
        "profile_id": "default",
        "station_id": default_station_id(),
        "line_id": os.getenv("AMX_LINE_ID", "line-01"),
        "recipe_id": "recipe-default",
        "name": "EOL Vision Standard",
        "description": "Commissioning profile for AI-vision EOL inspection.",
        "cameras": cameras,
        "checklist": {item: False for item in CHECKLIST_ITEMS},
        "checklist_confirmed_by": None,
        "checklist_confirmed_at": None,
        "acceptance": {
            "min_resolution_px": 1280,
            "min_views": 1,
            "require_bottom_view": False,
            "max_capture_gap_sec": 60,
            "png_for_training": True,
            "jpeg_ok_for_archive": True,
        },
        "updated_at": None,
        "cloned_from": None,
    }


class StationVisionStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        if not self.path.exists():
            return default_profile()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default_profile()
        merged = default_profile()
        merged.update({k: v for k, v in data.items() if k != "cameras"})
        if isinstance(data.get("cameras"), list) and data["cameras"]:
            merged["cameras"] = data["cameras"]
        if isinstance(data.get("checklist"), dict):
            merged["checklist"] = {**merged["checklist"], **data["checklist"]}
        return merged

    def save(self, payload: dict, *, actor: str | None = None) -> dict:
        profile = self._normalize(payload, actor=actor)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        return profile

    def _normalize(self, payload: dict, *, actor: str | None = None) -> dict:
        base = default_profile()
        if not isinstance(payload, dict):
            raise StationVisionError("profile must be an object")
        out = deepcopy(base)
        for key in (
            "profile_id",
            "station_id",
            "line_id",
            "recipe_id",
            "name",
            "description",
            "cloned_from",
        ):
            if payload.get(key):
                out[key] = str(payload[key]).strip()
        cameras_in = payload.get("cameras")
        if cameras_in is None:
            cameras_in = out["cameras"]
        if not isinstance(cameras_in, list) or not cameras_in:
            raise StationVisionError("at least one camera slot required")
        cap = max_cameras()
        if len(cameras_in) > HARD_CAP:
            raise StationVisionError(f"at most {HARD_CAP} camera slots (raise requires architecture review)")
        if len(cameras_in) > cap:
            raise StationVisionError(f"at most {cap} cameras (set AMX_MAX_CAMERAS, certified sequential path is 1–4)")
        cameras = []
        seen: set[str] = set()
        for idx, raw in enumerate(cameras_in, start=1):
            if not isinstance(raw, dict):
                raise StationVisionError(f"camera slot {idx} invalid")
            slot = _default_camera_slot(idx, raw.get("camera_id"))
            slot["camera_id"] = str(raw.get("camera_id") or slot["camera_id"]).strip()
            if not slot["camera_id"]:
                raise StationVisionError("camera_id required")
            if slot["camera_id"] in seen:
                raise StationVisionError(f"duplicate camera_id {slot['camera_id']}")
            seen.add(slot["camera_id"])
            role = str(raw.get("role") or slot["role"]).strip().lower()
            slot["role"] = role if role in CAMERA_ROLES else "other"
            slot["enabled"] = bool(raw.get("enabled", True))
            slot["lens_notes"] = str(raw.get("lens_notes") or "")
            slot["fov_notes"] = str(raw.get("fov_notes") or "")
            slot["working_distance_mm"] = raw.get("working_distance_mm")
            lighting = raw.get("lighting") if isinstance(raw.get("lighting"), dict) else {}
            slot["lighting"].update({k: lighting[k] for k in lighting if k != "light_controller"})
            trigger = str(slot["lighting"].get("trigger_mode") or "software").lower()
            slot["lighting"]["trigger_mode"] = trigger if trigger in TRIGGER_MODES else "software"
            ctrl = lighting.get("light_controller") if isinstance(lighting.get("light_controller"), dict) else {}
            slot["lighting"]["light_controller"].update(ctrl)
            capture = raw.get("capture") if isinstance(raw.get("capture"), dict) else {}
            slot["capture"].update(capture)
            fmt = str(slot["capture"].get("image_format") or "png").lower()
            slot["capture"]["image_format"] = fmt if fmt in IMAGE_FORMATS else "png"
            color = str(slot["capture"].get("color_mode") or "mono").lower()
            slot["capture"]["color_mode"] = color if color in COLOR_MODES else "mono"
            cameras.append(slot)
        out["cameras"] = cameras
        checklist = payload.get("checklist") if isinstance(payload.get("checklist"), dict) else {}
        for item in CHECKLIST_ITEMS:
            if item in checklist:
                out["checklist"][item] = bool(checklist[item])
        if payload.get("checklist_confirmed"):
            out["checklist_confirmed_by"] = actor
            out["checklist_confirmed_at"] = datetime.now(timezone.utc).isoformat()
        elif payload.get("checklist_confirmed_by"):
            out["checklist_confirmed_by"] = str(payload["checklist_confirmed_by"])
            out["checklist_confirmed_at"] = payload.get("checklist_confirmed_at")
        if isinstance(payload.get("acceptance"), dict):
            out["acceptance"].update(payload["acceptance"])
        out["updated_at"] = datetime.now(timezone.utc).isoformat()
        return out

    def export_text(self, *, fmt: str = "json") -> tuple[str, str]:
        profile = self.load()
        kind = (fmt or "json").strip().lower()
        if kind in {"yaml", "yml"}:
            return yaml_dumps(profile), "application/yaml"
        return json.dumps(profile, indent=2), "application/json"

    def import_text(self, body: str, *, actor: str | None = None) -> dict:
        text = (body or "").strip()
        if not text:
            raise StationVisionError("empty template")
        data: dict
        if text.startswith("{"):
            data = json.loads(text)
        else:
            loaded = yaml_loads(text)
            if not isinstance(loaded, dict):
                raise StationVisionError("template must be a mapping")
            data = loaded
        return self.save(data, actor=actor)

    def clone(self, *, new_station_id: str, new_name: str | None = None, actor: str | None = None) -> dict:
        current = self.load()
        cloned = deepcopy(current)
        cloned["cloned_from"] = current.get("station_id")
        cloned["station_id"] = str(new_station_id).strip()
        cloned["profile_id"] = f"clone-{uuid4().hex[:8]}"
        if new_name:
            cloned["name"] = new_name
        else:
            cloned["name"] = f"{current.get('name') or 'EOL'} ({cloned['station_id']})"
        cloned["checklist"] = {item: False for item in CHECKLIST_ITEMS}
        cloned["checklist_confirmed_by"] = None
        cloned["checklist_confirmed_at"] = None
        return self.save(cloned, actor=actor)


def camera_profile_for(profile: dict, camera_id: str) -> dict | None:
    for cam in profile.get("cameras") or []:
        if str(cam.get("camera_id")) == str(camera_id):
            return cam
    return None
