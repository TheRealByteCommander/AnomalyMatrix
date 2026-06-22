from __future__ import annotations

import os
from pathlib import Path


def build_repository(data_dir: Path):
    """JSONL for local/tests; Postgres when DATABASE_URL is set (Docker / production)."""
    dsn = os.getenv("DATABASE_URL", "").strip()
    if dsn:
        from .repository_postgres import PostgresResultRepository

        return PostgresResultRepository(dsn)
    from .repository import ResultRepository

    return ResultRepository(data_dir)
