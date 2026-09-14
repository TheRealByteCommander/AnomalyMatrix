"""Station camera selection for multi-view case inspection.

Certified sequential path: 1–4 cameras. Raise AMX_MAX_CAMERAS (≤16) for extra
slots (bottom / STF) — see docs/MULTI_CAMERA.md and AI_VISION_EOL_STANDARD.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from .camera_limits import CERTIFIED_MAX_CAMERAS, HARD_CAP, MIN_CAMERAS, max_cameras

# Back-compat alias used by tests and API payloads (evaluated at import).
MAX_CAMERAS = max_cameras()


class CameraSelectionError(ValueError):
    pass


class CameraStationStore:
    def __init__(self, path: Path):
        self.path = path

    def _default(self) -> dict:
        return {
            "camera_ids": ["cam-01"],
            "sources": {},
            "updated_at": None,
        }

    def load(self) -> dict:
        if not self.path.exists():
            return self._default()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default()
        ids = data.get("camera_ids") or ["cam-01"]
        if not isinstance(ids, list):
            ids = ["cam-01"]
        ids = [str(x).strip() for x in ids if str(x).strip()]
        if not ids:
            ids = ["cam-01"]
        sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
        cap = max_cameras()
        return {
            "camera_ids": ids[:cap],
            "sources": {str(k): str(v) for k, v in sources.items()},
            "updated_at": data.get("updated_at"),
            "max_cameras": cap,
            "certified_max_cameras": CERTIFIED_MAX_CAMERAS,
            "hard_cap": HARD_CAP,
        }

    def save(self, *, camera_ids: list[str], sources: dict[str, str] | None = None, available_ids: set[str] | None = None) -> dict:
        cleaned: list[str] = []
        seen: set[str] = set()
        for cam in camera_ids:
            cid = str(cam).strip()
            if not cid or cid in seen:
                continue
            seen.add(cid)
            cleaned.append(cid)

        cap = max_cameras()
        if len(cleaned) < MIN_CAMERAS:
            raise CameraSelectionError(f"At least {MIN_CAMERAS} camera required")
        if len(cleaned) > cap:
            raise CameraSelectionError(
                f"At most {cap} cameras allowed (certified sequential path is 1–{CERTIFIED_MAX_CAMERAS}; "
                f"raise AMX_MAX_CAMERAS up to {HARD_CAP})"
            )

        if available_ids is not None:
            unknown = [c for c in cleaned if c not in available_ids]
            if unknown:
                raise CameraSelectionError(f"Unknown cameras: {', '.join(unknown)}")

        from datetime import datetime, timezone

        src = {str(k): str(v) for k, v in (sources or {}).items() if str(k) in cleaned}
        data = {
            "camera_ids": cleaned,
            "sources": src,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "max_cameras": cap,
            "certified_max_cameras": CERTIFIED_MAX_CAMERAS,
            "hard_cap": HARD_CAP,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
