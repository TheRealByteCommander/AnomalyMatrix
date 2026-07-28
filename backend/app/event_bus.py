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
        views = result.get("views") if isinstance(result.get("views"), list) else []
        compact_views = [
            {
                "camera_id": v.get("camera_id"),
                "anomaly_score": (v.get("inference") or {}).get("anomaly_score"),
                "decision": v.get("decision"),
            }
            for v in views
        ]
        return self.emit(
            "InspectionCompleted",
            {
                "inspection_id": result.get("inspection_id"),
                "recipe_id": frame.get("recipe_id"),
                "camera_id": frame.get("camera_id"),
                "worst_view_camera_id": result.get("worst_view_camera_id") or frame.get("camera_id"),
                "camera_ids": result.get("camera_ids") or ([frame.get("camera_id")] if frame.get("camera_id") else []),
                "view_count": result.get("view_count") or max(1, len(compact_views)),
                "decision_policy": result.get("decision_policy") or "single",
                "views": compact_views,
                "anomaly_score": inference.get("anomaly_score"),
                "decision": result.get("decision"),
                "model_version": inference.get("model_version"),
                "provider": inference.get("provider"),
                "latency_ms": round(latency_ms, 2),
                "opcua_published": bool(opcua.get("published")),
                "heatmap_uri": result.get("heatmap", {}).get("uri"),
                "trend_warning": bool(result.get("trend_warning")),
                "drifting_camera_id": result.get("drifting_camera_id"),
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
