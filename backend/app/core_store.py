from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from .auth_tokens import create_session_id, hash_password, verify_password
from .production import is_production

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
        self._sessions_file = self.data_root / "sessions.json"
        if not self.use_postgres:
            self._seed_json_fallback()

    @property
    def use_postgres(self) -> bool:
        return bool(self.dsn and psycopg2 is not None)

    def _connect(self):
        if not self.use_postgres:
            raise RuntimeError("Postgres not configured")
        from .db_pool import pooled_connection

        return pooled_connection(self.dsn)  # type: ignore[arg-type]

    def _seed_json_fallback(self) -> None:
        if not self._users_file.exists():
            users = [
                {"user_id": "operator-1", "display_name": "Line Operator", "role_id": "operator", "api_key": "amx-key-operator", "active": True},
                {"user_id": "qa-1", "display_name": "QA Lead", "role_id": "qa_lead", "api_key": "amx-key-qa", "active": True},
                {"user_id": "engineer-1", "display_name": "Process Engineer", "role_id": "process_engineer", "api_key": "amx-key-engineer", "active": True},
                {"user_id": "admin-1", "display_name": "System Admin", "role_id": "admin", "api_key": "amx-key-admin", "active": True},
            ]
            if not is_production():
                default_password = hash_password("changeme")
                for user in users:
                    user["password_hash"] = default_password
            self._users_file.write_text(json.dumps(users, indent=2), encoding="utf-8")
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

    def get_user_by_id(self, user_id: str) -> dict | None:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT user_id, display_name, role_id, active, password_hash FROM users WHERE user_id = %s AND active = TRUE",
                        (user_id,),
                    )
                    row = cur.fetchone()
                    return dict(row) if row else None
        for user in json.loads(self._users_file.read_text(encoding="utf-8")):
            if user.get("user_id") == user_id and user.get("active", True):
                return user
        return None

    def authenticate_user(self, user_id: str, password: str) -> dict | None:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        stored = user.get("password_hash")
        if not stored or not verify_password(password, stored):
            return None
        return user

    def set_user_password(self, user_id: str, password: str) -> bool:
        password_hash = hash_password(password)
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET password_hash = %s WHERE user_id = %s AND active = TRUE",
                        (password_hash, user_id),
                    )
                    updated = cur.rowcount > 0
                conn.commit()
                return updated
        users = json.loads(self._users_file.read_text(encoding="utf-8"))
        found = False
        for user in users:
            if user.get("user_id") == user_id and user.get("active", True):
                user["password_hash"] = password_hash
                found = True
                break
        if found:
            self._users_file.write_text(json.dumps(users, indent=2), encoding="utf-8")
        return found

    def create_session(self, user_id: str, *, ttl_sec: int = 28800) -> dict:
        from datetime import datetime, timedelta, timezone

        session_id = create_session_id()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
        entry = {"session_id": session_id, "user_id": user_id, "expires_at": expires_at.isoformat()}
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (%s,%s,%s)",
                        (session_id, user_id, expires_at),
                    )
                conn.commit()
        else:
            sessions = []
            if self._sessions_file.exists():
                sessions = json.loads(self._sessions_file.read_text(encoding="utf-8"))
            sessions.append(entry)
            self._sessions_file.write_text(json.dumps(sessions, indent=2), encoding="utf-8")
        return entry

    def get_session(self, session_id: str) -> dict | None:
        from datetime import datetime, timezone

        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT session_id, user_id, expires_at FROM sessions WHERE session_id = %s",
                        (session_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    if row["expires_at"] < datetime.now(timezone.utc):
                        return None
                    return dict(row)
        if not self._sessions_file.exists():
            return None
        now = datetime.now(timezone.utc)
        for entry in json.loads(self._sessions_file.read_text(encoding="utf-8")):
            if entry.get("session_id") != session_id:
                continue
            expires = datetime.fromisoformat(entry["expires_at"])
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < now:
                return None
            return entry
        return None

    def revoke_session(self, session_id: str) -> None:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
                conn.commit()
            return
        if not self._sessions_file.exists():
            return
        sessions = [s for s in json.loads(self._sessions_file.read_text(encoding="utf-8")) if s.get("session_id") != session_id]
        self._sessions_file.write_text(json.dumps(sessions, indent=2), encoding="utf-8")

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

    def get_model(self, model_id: str) -> dict | None:
        for item in self.list_models():
            if item.get("model_id") == model_id:
                return item
        return None

    def get_active_model(self) -> dict | None:
        models = self.list_models()
        for item in models:
            if item.get("status") == "active":
                return item
        return models[0] if models else None

    def register_model(self, entry: dict) -> dict:
        payload = {
            "model_id": entry["model_id"],
            "name": entry["name"],
            "model_version": entry["model_version"],
            "provider": entry.get("provider", "patchcore"),
            "dataset_version": entry.get("dataset_version", "v1"),
            "status": entry.get("status", "candidate"),
            "metadata": entry.get("metadata", {}),
        }
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO model_registry (model_id, name, model_version, provider, dataset_version, status, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (model_id) DO UPDATE SET
                          name = EXCLUDED.name,
                          model_version = EXCLUDED.model_version,
                          provider = EXCLUDED.provider,
                          dataset_version = EXCLUDED.dataset_version,
                          status = EXCLUDED.status,
                          metadata = EXCLUDED.metadata
                        RETURNING model_id, name, model_version, provider, dataset_version, status, metadata
                        """,
                        (
                            payload["model_id"],
                            payload["name"],
                            payload["model_version"],
                            payload["provider"],
                            payload["dataset_version"],
                            payload["status"],
                            Json(payload["metadata"]),
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
                return dict(row) if row else payload
        models = self.list_models()
        models = [m for m in models if m.get("model_id") != payload["model_id"]]
        models.insert(0, payload)
        self._models_file.write_text(json.dumps(models, indent=2), encoding="utf-8")
        return payload

    def promote_model(self, model_id: str) -> dict:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("UPDATE model_registry SET status = 'archived' WHERE status = 'active'")
                    cur.execute(
                        "UPDATE model_registry SET status = 'active' WHERE model_id = %s RETURNING *",
                        (model_id,),
                    )
                    row = cur.fetchone()
                conn.commit()
                if not row:
                    raise ValueError(f"Model not found: {model_id}")
                return dict(row)
        models = self.list_models()
        found = None
        for item in models:
            if item.get("model_id") == model_id:
                found = item
                item["status"] = "active"
            elif item.get("status") == "active":
                item["status"] = "archived"
        if not found:
            raise ValueError(f"Model not found: {model_id}")
        self._models_file.write_text(json.dumps(models, indent=2), encoding="utf-8")
        return found

    def rollback_model(self) -> dict | None:
        models = self.list_models()
        active = next((m for m in models if m.get("status") == "active"), None)
        if not active:
            return None
        previous = next((m for m in models if m.get("status") == "archived"), None)
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("UPDATE model_registry SET status = 'rolled_back' WHERE model_id = %s", (active["model_id"],))
                    if previous:
                        cur.execute(
                            "UPDATE model_registry SET status = 'active' WHERE model_id = %s RETURNING *",
                            (previous["model_id"],),
                        )
                        row = cur.fetchone()
                    else:
                        row = None
                conn.commit()
                return dict(row) if row else None
        for item in models:
            if item.get("model_id") == active.get("model_id"):
                item["status"] = "rolled_back"
        restored = None
        if previous:
            for item in models:
                if item.get("model_id") == previous.get("model_id"):
                    item["status"] = "active"
                    restored = item
        self._models_file.write_text(json.dumps(models, indent=2), encoding="utf-8")
        return restored

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
