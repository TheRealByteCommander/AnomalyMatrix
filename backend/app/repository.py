from __future__ import annotations

from pathlib import Path
from threading import Lock
import json


class ResultRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.results_file = self.root / 'inspection_results.jsonl'
        self._lock = Lock()

    def append(self, payload: dict) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        with self._lock:
            with self.results_file.open('a', encoding='utf-8') as f:
                f.write(line + '\n')

    def _read_all(self) -> list[dict]:
        if not self.results_file.exists():
            return []
        lines = self.results_file.read_text(encoding='utf-8').splitlines()
        out = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def latest(self, limit: int = 20) -> list[dict]:
        out = self._read_all()
        return list(reversed(out[-limit:]))

    def query(self, *, recipe_id: str | None = None, min_score: float | None = None, max_score: float | None = None, limit: int = 50) -> list[dict]:
        items = self._read_all()
        filtered = []
        for item in items:
            frame = item.get('frame', {})
            inf = item.get('inference', {})
            score = inf.get('anomaly_score', 0.0)
            if recipe_id and frame.get('recipe_id') != recipe_id:
                continue
            if min_score is not None and score < min_score:
                continue
            if max_score is not None and score > max_score:
                continue
            filtered.append(item)
        return list(reversed(filtered[-limit:]))

    def trend_summary(self) -> dict:
        items = self._read_all()
        if not items:
            return {"count": 0, "avg_score": 0.0, "max_score": 0.0, "anomaly_count": 0}
        scores = [float(i.get('inference', {}).get('anomaly_score', 0.0)) for i in items]
        anomaly_count = sum(1 for i in items if i.get('inference', {}).get('status') == 'anomaly')
        return {
            "count": len(items),
            "avg_score": round(sum(scores) / len(scores), 4),
            "max_score": round(max(scores), 4),
            "anomaly_count": anomaly_count,
        }
