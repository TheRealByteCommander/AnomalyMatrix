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

    def latest(self, limit: int = 20) -> list[dict]:
        if not self.results_file.exists():
            return []
        lines = self.results_file.read_text(encoding='utf-8').splitlines()
        out = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(out))
