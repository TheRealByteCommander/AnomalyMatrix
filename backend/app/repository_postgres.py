from __future__ import annotations

import json
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from .trend_warnings import enrich_trend_summary


class PostgresResultRepository:
    """Postgres-backed inspection store (Phase 3). Falls back not required here."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._ensure_schema()

    def _connect(self):
        return psycopg2.connect(self.dsn)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS inspections (
                      inspection_id UUID PRIMARY KEY,
                      camera_id TEXT NOT NULL,
                      recipe_id TEXT NOT NULL,
                      anomaly_score DOUBLE PRECISION NOT NULL,
                      status TEXT NOT NULL,
                      decision TEXT NOT NULL,
                      provider TEXT NOT NULL,
                      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                      payload JSONB
                    );
                    """
                )
                cur.execute("ALTER TABLE inspections ADD COLUMN IF NOT EXISTS payload JSONB;")
            conn.commit()

    def append(self, payload: dict) -> None:
        frame = payload.get("frame", {})
        inf = payload.get("inference", {})
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inspections
                      (inspection_id, camera_id, recipe_id, anomaly_score, status, decision, provider, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (inspection_id) DO UPDATE SET payload = EXCLUDED.payload
                    """,
                    (
                        payload.get("inspection_id"),
                        frame.get("camera_id", "unknown"),
                        frame.get("recipe_id", "unknown"),
                        float(inf.get("anomaly_score", 0.0)),
                        inf.get("status", "unknown"),
                        payload.get("decision", "green"),
                        inf.get("provider", "stub"),
                        Json(payload),
                    ),
                )
            conn.commit()

    def _rows_to_items(self, rows: list[dict]) -> list[dict]:
        items: list[dict] = []
        for row in rows:
            raw = row.get("payload")
            if isinstance(raw, dict):
                items.append(raw)
            elif isinstance(raw, str):
                items.append(json.loads(raw))
        return items

    def latest(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT payload FROM inspections
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return self._rows_to_items(rows)

    def query(
        self,
        *,
        recipe_id: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        limit: int = 50,
    ) -> list[dict]:
        clauses = ["1=1"]
        params: list[Any] = []
        if recipe_id:
            clauses.append("recipe_id = %s")
            params.append(recipe_id)
        if min_score is not None:
            clauses.append("anomaly_score >= %s")
            params.append(min_score)
        if max_score is not None:
            clauses.append("anomaly_score <= %s")
            params.append(max_score)
        params.append(limit)
        sql = f"""
            SELECT payload FROM inspections
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT %s
        """
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return self._rows_to_items(rows)

    def trend_summary(self) -> dict:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                      COUNT(*) AS count,
                      COALESCE(AVG(anomaly_score), 0) AS avg_score,
                      COALESCE(MAX(anomaly_score), 0) AS max_score,
                      COALESCE(SUM(CASE WHEN status = 'anomaly' THEN 1 ELSE 0 END), 0) AS anomaly_count
                    FROM inspections
                    """
                )
                row = cur.fetchone() or {}
        base = {
            "count": int(row.get("count", 0)),
            "avg_score": round(float(row.get("avg_score", 0.0)), 4),
            "max_score": round(float(row.get("max_score", 0.0)), 4),
            "anomaly_count": int(row.get("anomaly_count", 0)),
        }
        recent = list(reversed(self.latest(limit=50)))
        return enrich_trend_summary(base, recent)
