from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


class DomainEventBus:
    """Append-only domain event log (BUILD_READY_SPEC v1)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_file = self.root / "domain_events.jsonl"
        self._lock = Lock()

    def emit(self, event_type: str, payload: dict) -> dict:
        event = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "schema_version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with self.events_file.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return event

    def emit_inspection_completed(self, result: dict, *, latency_ms: float) -> dict:
        frame = result.get("frame", {})
        inference = result.get("inference", {})
        opcua = result.get("opcua_publish", {})
        return self.emit(
            "InspectionCompleted",
            {
                "inspection_id": result.get("inspection_id"),
                "recipe_id": frame.get("recipe_id"),
                "camera_id": frame.get("camera_id"),
                "anomaly_score": inference.get("anomaly_score"),
                "decision": result.get("decision"),
                "model_version": inference.get("model_version"),
                "provider": inference.get("provider"),
                "latency_ms": round(latency_ms, 2),
                "opcua_published": bool(opcua.get("published")),
                "heatmap_uri": result.get("heatmap", {}).get("uri"),
            },
        )

    def recent(self, limit: int = 50) -> list[dict]:
        if not self.events_file.exists():
            return []
        lines = self.events_file.read_text(encoding="utf-8").splitlines()
        out: list[dict] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(out))
