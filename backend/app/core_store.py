from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    RealDictCursor = None  # type: ignore
    Json = None  # type: ignore


class CoreStore:
    """Recipes, RBAC users, audit log, model registry, feedback — Postgres or JSONL fallback."""

    def __init__(self, data_root: Path, dsn: str | None = None) -> None:
        self.data_root = data_root
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.dsn = dsn or os.getenv("DATABASE_URL", "").strip() or None
        self._lock = Lock()
        self._audit_file = self.data_root / "audit_log.jsonl"
        self._feedback_file = self.data_root / "feedback_events.jsonl"
        self._recipes_file = self.data_root / "recipes.json"
        self._models_file = self.data_root / "model_registry.json"
        self._users_file = self.data_root / "users.json"
        if not self.use_postgres:
            self._seed_json_fallback()

    @property
    def use_postgres(self) -> bool:
        return bool(self.dsn and psycopg2 is not None)

    def _connect(self):
        if not self.use_postgres:
            raise RuntimeError("Postgres not configured")
        return psycopg2.connect(self.dsn)  # type: ignore[arg-type]

    def _seed_json_fallback(self) -> None:
        if not self._users_file.exists():
            self._users_file.write_text(
                json.dumps(
                    [
                        {"user_id": "operator-1", "display_name": "Line Operator", "role_id": "operator", "api_key": "amx-key-operator", "active": True},
                        {"user_id": "qa-1", "display_name": "QA Lead", "role_id": "qa_lead", "api_key": "amx-key-qa", "active": True},
                        {"user_id": "engineer-1", "display_name": "Process Engineer", "role_id": "process_engineer", "api_key": "amx-key-engineer", "active": True},
                        {"user_id": "admin-1", "display_name": "System Admin", "role_id": "admin", "api_key": "amx-key-admin", "active": True},
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not self._recipes_file.exists():
            self._recipes_file.write_text(
                json.dumps(
                    [{"recipe_id": "recipe-default", "name": "Default Seam Inspection", "recipe_version": "v1", "active": True}],
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not self._models_file.exists():
            self._models_file.write_text(
                json.dumps(
                    [{"model_id": "patchcore-mvp", "name": "PatchCore MVP", "model_version": "v0", "provider": "stub", "status": "active"}],
                    indent=2,
                ),
                encoding="utf-8",
            )

    def get_user_by_api_key(self, api_key: str) -> dict | None:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT user_id, display_name, role_id, active FROM users WHERE api_key = %s AND active = TRUE",
                        (api_key,),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        for user in json.loads(self._users_file.read_text(encoding="utf-8")):
            if user.get("api_key") == api_key and user.get("active", True):
                return user
        return None

    def list_recipes(self) -> list[dict]:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT recipe_id, name, recipe_version, active FROM recipes ORDER BY recipe_id")
                    return [dict(r) for r in cur.fetchall()]
        return json.loads(self._recipes_file.read_text(encoding="utf-8"))

    def list_models(self) -> list[dict]:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT model_id, name, model_version, provider, dataset_version, status FROM model_registry ORDER BY created_at DESC"
                    )
                    return [dict(r) for r in cur.fetchall()]
        return json.loads(self._models_file.read_text(encoding="utf-8"))

    def append_audit(
        self,
        *,
        actor: str,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        before_state: dict | None = None,
        after_state: dict | None = None,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        entry = {
            "audit_id": str(uuid4()),
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "before_state": before_state,
            "after_state": after_state,
            "reason": reason,
            "request_id": request_id,
        }
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO audit_log (audit_id, actor, action, resource_type, resource_id, before_state, after_state, reason, request_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING audit_id, created_at
                        """,
                        (
                            entry["audit_id"],
                            actor,
                            action,
                            resource_type,
                            resource_id,
                            Json(before_state) if before_state else None,
                            Json(after_state) if after_state else None,
                            reason,
                            request_id,
                        ),
                    )
                    row = cur.fetchone()
                    entry["created_at"] = row["created_at"].isoformat() if row else None
                conn.commit()
        else:
            with self._lock:
                with self._audit_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def append_feedback(
        self,
        *,
        inspection_id: str,
        actor: str,
        verdict: str,
        comment: str = "",
        recipe_version: str = "v1",
        model_version: str = "v0",
    ) -> dict:
        entry = {
            "feedback_id": str(uuid4()),
            "inspection_id": inspection_id,
            "actor": actor,
            "verdict": verdict,
            "comment": comment,
            "recipe_version": recipe_version,
            "model_version": model_version,
        }
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO feedback_events (feedback_id, inspection_id, actor, verdict, comment, recipe_version, model_version)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        RETURNING feedback_id, created_at
                        """,
                        (entry["feedback_id"], inspection_id, actor, verdict, comment, recipe_version, model_version),
                    )
                    row = cur.fetchone()
                    entry["created_at"] = row["created_at"].isoformat() if row else None
                conn.commit()
        else:
            with self._lock:
                with self._feedback_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def list_feedback(self, *, inspection_id: str | None = None, limit: int = 50) -> list[dict]:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if inspection_id:
                        cur.execute(
                            "SELECT * FROM feedback_events WHERE inspection_id = %s ORDER BY created_at DESC LIMIT %s",
                            (inspection_id, limit),
                        )
                    else:
                        cur.execute("SELECT * FROM feedback_events ORDER BY created_at DESC LIMIT %s", (limit,))
                    return [dict(r) for r in cur.fetchall()]
        if not self._feedback_file.exists():
            return []
        items = []
        for line in self._feedback_file.read_text(encoding="utf-8").splitlines():
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if inspection_id:
            items = [i for i in items if i.get("inspection_id") == inspection_id]
        return list(reversed(items[-limit:]))
