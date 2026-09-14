from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from threading import Lock
from uuid import uuid4

from datetime import datetime, timezone

from .auth_tokens import create_session_id, hash_password, verify_password
from .decision import DEFAULT_THRESHOLDS, normalize_thresholds, validate_thresholds
from .production import is_production

PROTECTED_RECIPE_ID = "recipe-default"
RECIPE_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,62}$")
BOUND_MODEL_STATUSES = frozenset({"active", "candidate"})


class RecipeError(ValueError):
    status_code = 400


class RecipeNotFound(RecipeError):
    status_code = 404


class RecipeConflict(RecipeError):
    status_code = 409


def validate_recipe_id(recipe_id: str) -> str:
    cleaned = str(recipe_id or "").strip()
    if not RECIPE_ID_PATTERN.fullmatch(cleaned):
        raise RecipeError(
            "recipe_id must start with a letter and contain only letters, digits, '.', '_' or '-' (2–63 chars)"
        )
    return cleaned

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
        else:
            self._ensure_schema_extensions()

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
                    [
                        {
                            "recipe_id": PROTECTED_RECIPE_ID,
                            "name": "Default Seam Inspection",
                            "recipe_version": "v1",
                            "active": True,
                            "camera_profile": {"camera_id": "cam-01", "exposure_ms": 10},
                            "lighting_profile": {"gain_db": 2},
                            "decision_thresholds": dict(DEFAULT_THRESHOLDS),
                        }
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not self._models_file.exists():
            self._models_file.write_text(
                json.dumps(
                    [
                        {
                            "model_id": "patchcore-mvp",
                            "name": "PatchCore MVP",
                            "model_version": "v0",
                            "provider": "stub",
                            "status": "active",
                            "dataset_version": "v1",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "metadata": {},
                        }
                    ],
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

    def _ensure_schema_extensions(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    ALTER TABLE recipes
                    ADD COLUMN IF NOT EXISTS decision_thresholds JSONB
                    NOT NULL DEFAULT '{"amber": 0.55, "red": 0.85}'::jsonb
                    """
                )
            conn.commit()

    _RECIPE_COLUMNS = (
        "recipe_id, name, recipe_version, camera_profile, lighting_profile, active, decision_thresholds"
    )

    @staticmethod
    def _as_object(value, default: dict | None = None) -> dict:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return dict(default or {})
            return dict(parsed) if isinstance(parsed, dict) else dict(default or {})
        return dict(default or {})

    @classmethod
    def _serialize_recipe(cls, recipe: dict) -> dict:
        item = dict(recipe)
        item["decision_thresholds"] = normalize_thresholds(item.get("decision_thresholds"))
        item["camera_profile"] = cls._as_object(item.get("camera_profile"))
        item["lighting_profile"] = cls._as_object(item.get("lighting_profile"))
        item["active"] = bool(item.get("active", False))
        item["status"] = "active" if item["active"] else "inactive"
        item["protected"] = item.get("recipe_id") == PROTECTED_RECIPE_ID
        return item

    def list_recipes(self) -> list[dict]:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(f"SELECT {self._RECIPE_COLUMNS} FROM recipes ORDER BY recipe_id")
                    return [self._serialize_recipe(dict(r)) for r in cur.fetchall()]
        recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
        return [self._serialize_recipe(item) for item in recipes]

    def get_recipe(self, recipe_id: str) -> dict | None:
        for recipe in self.list_recipes():
            if recipe.get("recipe_id") == recipe_id:
                return recipe
        return None

    def get_decision_thresholds(self, recipe_id: str) -> dict:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return dict(DEFAULT_THRESHOLDS)
        return normalize_thresholds(recipe.get("decision_thresholds"))

    def _write_recipes_json(self, recipes: list[dict]) -> None:
        with self._lock:
            self._recipes_file.write_text(json.dumps(recipes, indent=2), encoding="utf-8")

    def _require_recipe(self, recipe_id: str) -> dict:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise RecipeNotFound(f"Recipe not found: {recipe_id}")
        return recipe

    @staticmethod
    def _normalize_profile(raw) -> dict:
        if raw is None:
            return {}
        if not isinstance(raw, dict):
            raise RecipeError("camera_profile and lighting_profile must be objects")
        out: dict = {}
        for key, value in raw.items():
            name = str(key).strip()
            if not name or name.startswith("_"):
                continue
            out[name] = value
        return out

    def _normalize_recipe_fields(
        self,
        *,
        name: str | None = None,
        recipe_version: str | None = None,
        active: bool | None = None,
        camera_profile=None,
        lighting_profile=None,
        amber: float | None = None,
        red: float | None = None,
        existing: dict | None = None,
    ) -> dict:
        base = dict(existing or {})
        display = str(name if name is not None else base.get("name") or "").strip()
        if not display:
            raise RecipeError("name is required")
        if len(display) > 128:
            raise RecipeError("name must be at most 128 characters")
        version = str(recipe_version if recipe_version is not None else base.get("recipe_version") or "v1").strip() or "v1"
        if len(version) > 32:
            raise RecipeError("recipe_version must be at most 32 characters")
        thresholds = normalize_thresholds(base.get("decision_thresholds"))
        if amber is not None or red is not None:
            thresholds = validate_thresholds(
                amber if amber is not None else thresholds["amber"],
                red if red is not None else thresholds["red"],
            )
        camera = self._normalize_profile(
            camera_profile if camera_profile is not None else base.get("camera_profile")
        )
        lighting = self._normalize_profile(
            lighting_profile if lighting_profile is not None else base.get("lighting_profile")
        )
        is_active = bool(base.get("active", False) if active is None else active)
        return {
            "name": display,
            "recipe_version": version,
            "active": is_active,
            "camera_profile": camera,
            "lighting_profile": lighting,
            "decision_thresholds": thresholds,
        }

    def models_bound_to_recipe(self, recipe_id: str) -> list[dict]:
        bound = []
        for model in self.list_models():
            meta = model.get("metadata") if isinstance(model.get("metadata"), dict) else {}
            if meta.get("recipe_id") != recipe_id:
                continue
            if model.get("status") in BOUND_MODEL_STATUSES:
                bound.append(model)
        return bound

    def archive_recipe_assets(self, recipe_id: str) -> dict:
        """Move training / n.i.O. banks aside so delete does not orphan live folders."""
        from .nio_store import nio_images_dir, safe_id
        from .training_service import training_images_dir

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest_root = self.data_root / "archived-recipes" / safe_id(recipe_id) / ts
        moved: list[dict] = []
        sources = (
            ("training-images", training_images_dir(self.data_root, recipe_id)),
            ("nio-images", nio_images_dir(self.data_root, recipe_id)),
        )
        for kind, src in sources:
            if not src.exists():
                continue
            try:
                has_files = any(src.iterdir())
            except OSError:
                has_files = True
            if not has_files:
                continue
            dest = dest_root / kind
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            moved.append({"kind": kind, "from": str(src), "to": str(dest)})
        return {"archived_at": ts, "moved": moved}

    def _deactivate_other_recipes(self, keep_id: str) -> None:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE recipes SET active = FALSE, updated_at = NOW() WHERE recipe_id <> %s AND active = TRUE",
                        (keep_id,),
                    )
                conn.commit()
            return
        recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
        changed = False
        for item in recipes:
            if item.get("recipe_id") != keep_id and item.get("active"):
                item["active"] = False
                changed = True
        if changed:
            self._write_recipes_json(recipes)

    def _activate_fallback(self, excluded_id: str) -> str | None:
        remaining = [r for r in self.list_recipes() if r.get("recipe_id") != excluded_id]
        if not remaining:
            return None
        fallback = next((r for r in remaining if r.get("recipe_id") == PROTECTED_RECIPE_ID), remaining[0])
        fid = fallback["recipe_id"]
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE recipes SET active = TRUE, updated_at = NOW() WHERE recipe_id = %s",
                        (fid,),
                    )
                conn.commit()
        else:
            recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
            for item in recipes:
                if item.get("recipe_id") == fid:
                    item["active"] = True
            self._write_recipes_json(recipes)
        return fid

    def create_recipe(
        self,
        *,
        recipe_id: str,
        name: str,
        recipe_version: str = "v1",
        active: bool = False,
        camera_profile: dict | None = None,
        lighting_profile: dict | None = None,
        amber: float | None = None,
        red: float | None = None,
    ) -> dict:
        recipe_id = validate_recipe_id(recipe_id)
        if self.get_recipe(recipe_id):
            raise RecipeConflict(f"Recipe already exists: {recipe_id}")
        fields = self._normalize_recipe_fields(
            name=name,
            recipe_version=recipe_version,
            active=active,
            camera_profile=camera_profile if camera_profile is not None else {},
            lighting_profile=lighting_profile if lighting_profile is not None else {},
            amber=amber,
            red=red,
        )
        payload = {"recipe_id": recipe_id, **fields}
        if self.use_postgres:
            try:
                with self._connect() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(
                            f"""
                            INSERT INTO recipes ({self._RECIPE_COLUMNS})
                            VALUES (%s,%s,%s,%s,%s,%s,%s)
                            RETURNING {self._RECIPE_COLUMNS}
                            """,
                            (
                                recipe_id,
                                fields["name"],
                                fields["recipe_version"],
                                Json(fields["camera_profile"]),
                                Json(fields["lighting_profile"]),
                                fields["active"],
                                Json(fields["decision_thresholds"]),
                            ),
                        )
                        row = cur.fetchone()
                    conn.commit()
            except Exception as exc:
                if psycopg2 is not None and isinstance(exc, psycopg2.IntegrityError):
                    raise RecipeConflict(f"Recipe already exists: {recipe_id}") from exc
                raise
            created = self._serialize_recipe(dict(row) if row else payload)
        else:
            recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
            recipes.append(payload)
            self._write_recipes_json(recipes)
            created = self._serialize_recipe(payload)
        if fields["active"]:
            self._deactivate_other_recipes(recipe_id)
            created["active"] = True
            created["status"] = "active"
        return created

    def update_recipe(
        self,
        recipe_id: str,
        *,
        name: str | None = None,
        recipe_version: str | None = None,
        active: bool | None = None,
        camera_profile=None,
        lighting_profile=None,
        amber: float | None = None,
        red: float | None = None,
    ) -> dict:
        existing = self._require_recipe(recipe_id)
        fields = self._normalize_recipe_fields(
            name=name,
            recipe_version=recipe_version,
            active=active,
            camera_profile=camera_profile,
            lighting_profile=lighting_profile,
            amber=amber,
            red=red,
            existing=existing,
        )
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        f"""
                        UPDATE recipes
                        SET name = %s, recipe_version = %s, camera_profile = %s, lighting_profile = %s,
                            active = %s, decision_thresholds = %s, updated_at = NOW()
                        WHERE recipe_id = %s
                        RETURNING {self._RECIPE_COLUMNS}
                        """,
                        (
                            fields["name"],
                            fields["recipe_version"],
                            Json(fields["camera_profile"]),
                            Json(fields["lighting_profile"]),
                            fields["active"],
                            Json(fields["decision_thresholds"]),
                            recipe_id,
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
                if not row:
                    raise RecipeNotFound(f"Recipe not found: {recipe_id}")
                updated = self._serialize_recipe(dict(row))
        else:
            recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
            found = None
            for item in recipes:
                if item.get("recipe_id") == recipe_id:
                    item.update(fields)
                    found = item
                    break
            if not found:
                raise RecipeNotFound(f"Recipe not found: {recipe_id}")
            self._write_recipes_json(recipes)
            updated = self._serialize_recipe(found)
        if fields["active"]:
            self._deactivate_other_recipes(recipe_id)
            updated["active"] = True
            updated["status"] = "active"
        return updated

    def update_recipe_thresholds(self, recipe_id: str, *, amber: float, red: float) -> dict:
        return self.update_recipe(recipe_id, amber=amber, red=red)

    def delete_recipe(
        self,
        recipe_id: str,
        *,
        confirm: bool = False,
        confirm_recipe_id: str = "",
    ) -> dict:
        recipe_id = str(recipe_id or "").strip()
        existing = self._require_recipe(recipe_id)
        if not confirm or str(confirm_recipe_id or "").strip() != recipe_id:
            raise RecipeError(
                "Double confirmation required: set confirm=true and confirm_recipe_id to the recipe id"
            )
        if recipe_id == PROTECTED_RECIPE_ID:
            raise RecipeConflict(
                f"{PROTECTED_RECIPE_ID} is a protected system recipe and cannot be deleted"
            )
        remaining = [r for r in self.list_recipes() if r.get("recipe_id") != recipe_id]
        if not remaining:
            raise RecipeConflict("Cannot delete the last remaining recipe")
        bound = self.models_bound_to_recipe(recipe_id)
        if bound:
            ids = ", ".join(str(m.get("model_id")) for m in bound[:8])
            raise RecipeConflict(
                "Cannot delete recipe while active or candidate models reference it "
                f"({ids}). Promote or activate another model first."
            )
        archived = self.archive_recipe_assets(recipe_id)
        fallback = None
        if existing.get("active"):
            fallback = self._activate_fallback(recipe_id)
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM recipes WHERE recipe_id = %s", (recipe_id,))
                    deleted = cur.rowcount
                conn.commit()
            if not deleted:
                raise RecipeNotFound(f"Recipe not found: {recipe_id}")
        else:
            recipes = json.loads(self._recipes_file.read_text(encoding="utf-8"))
            next_recipes = [item for item in recipes if item.get("recipe_id") != recipe_id]
            if len(next_recipes) == len(recipes):
                raise RecipeNotFound(f"Recipe not found: {recipe_id}")
            self._write_recipes_json(next_recipes)
        return {
            "deleted": True,
            "recipe_id": recipe_id,
            "recipe": existing,
            "archived_assets": archived,
            "activated_fallback": fallback,
        }

    @staticmethod
    def _serialize_model(row: dict | None) -> dict | None:
        if not row:
            return None
        item = dict(row)
        created = item.get("created_at")
        if hasattr(created, "isoformat"):
            item["created_at"] = created.isoformat()
        meta = item.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        item["metadata"] = meta if isinstance(meta, dict) else {}
        return item

    def list_models(self) -> list[dict]:
        if self.use_postgres:
            with self._connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT model_id, name, model_version, provider, dataset_version, status, metadata, created_at
                        FROM model_registry
                        ORDER BY created_at DESC
                        """
                    )
                    return [self._serialize_model(dict(r)) or {} for r in cur.fetchall()]
        if not self._models_file.exists():
            return []
        items = json.loads(self._models_file.read_text(encoding="utf-8"))
        return [self._serialize_model(item) or {} for item in items]

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
            "created_at": entry.get("created_at") or datetime.now(timezone.utc).isoformat(),
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
                        RETURNING model_id, name, model_version, provider, dataset_version, status, metadata, created_at
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
                return self._serialize_model(dict(row)) if row else payload
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
                        """
                        UPDATE model_registry SET status = 'active' WHERE model_id = %s
                        RETURNING model_id, name, model_version, provider, dataset_version, status, metadata, created_at
                        """,
                        (model_id,),
                    )
                    row = cur.fetchone()
                conn.commit()
                if not row:
                    raise ValueError(f"Model not found: {model_id}")
                return self._serialize_model(dict(row)) or {}
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
                            """
                            UPDATE model_registry SET status = 'active' WHERE model_id = %s
                            RETURNING model_id, name, model_version, provider, dataset_version, status, metadata, created_at
                            """,
                            (previous["model_id"],),
                        )
                        row = cur.fetchone()
                    else:
                        row = None
                conn.commit()
                return self._serialize_model(dict(row)) if row else None
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
