"""Capture watchdog, gap detection, and stack self-test status."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

_lock = threading.Lock()
_DEFAULT_INTERVAL_SEC = 30.0


class CaptureWatchdog:
    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> dict:
        if not self.path.exists():
            return {
                "last_capture_at": None,
                "last_inspection_id": None,
                "last_epc": None,
                "last_trigger_source": None,
                "capture_count": 0,
                "gap_count": 0,
                "last_gap_at": None,
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "last_capture_at": None,
                "last_inspection_id": None,
                "last_epc": None,
                "last_trigger_source": None,
                "capture_count": 0,
                "gap_count": 0,
                "last_gap_at": None,
            }

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def expected_interval_sec(self) -> float:
        raw = os.getenv("AMX_CAPTURE_WATCHDOG_SEC", str(_DEFAULT_INTERVAL_SEC)).strip()
        try:
            return max(1.0, float(raw))
        except ValueError:
            return _DEFAULT_INTERVAL_SEC

    def record(self, *, inspection_id: str, epc: str | None, trigger_source: str) -> dict:
        now = datetime.now(timezone.utc)
        with _lock:
            data = self._load()
            last = data.get("last_capture_at")
            if last:
                try:
                    prev = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                    delta = (now - prev).total_seconds()
                    if delta > self.expected_interval_sec() * 2:
                        data["gap_count"] = int(data.get("gap_count") or 0) + 1
                        data["last_gap_at"] = now.isoformat()
                        data["last_gap_sec"] = round(delta, 3)
                except ValueError:
                    pass
            data["last_capture_at"] = now.isoformat()
            data["last_inspection_id"] = inspection_id
            data["last_epc"] = epc
            data["last_trigger_source"] = trigger_source
            data["capture_count"] = int(data.get("capture_count") or 0) + 1
            self._save(data)
            return data

    def snapshot(self) -> dict:
        with _lock:
            data = self._load()
        now = datetime.now(timezone.utc)
        last = data.get("last_capture_at")
        age = None
        gap = False
        if last:
            try:
                prev = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                age = round((now - prev).total_seconds(), 3)
                gap = age > self.expected_interval_sec() * 2
            except ValueError:
                age = None
        status = "ok"
        if last is None:
            status = "idle"
        elif gap:
            status = "gap"
        return {
            **data,
            "expected_interval_sec": self.expected_interval_sec(),
            "seconds_since_last_capture": age,
            "gap_detected": gap,
            "status": status,
            "endurance_hint": "Health, watchdog and gap detection support ≥24h unattended runs.",
        }
