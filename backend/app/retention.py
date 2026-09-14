"""Retention / archive / deletion policy for capture artifacts."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .storage_layout import SCHEMA_VERSION

DEFAULT_TTL_DAYS = 90


def default_policy() -> dict:
    return {
        "schema": "RetentionPolicy",
        "schema_version": SCHEMA_VERSION,
        "ttl_days": int(os.getenv("AMX_RETENTION_TTL_DAYS", str(DEFAULT_TTL_DAYS)) or DEFAULT_TTL_DAYS),
        "archive_bucket": os.getenv("MINIO_ARCHIVE_BUCKET", "archive-images").strip() or "archive-images",
        "archive_prefix": os.getenv("AMX_ARCHIVE_PREFIX", "eol/").strip() or "eol/",
        "legal_hold_default": os.getenv("AMX_LEGAL_HOLD", "").strip().lower() in {"1", "true", "yes"},
        "delete_after_archive": os.getenv("AMX_DELETE_AFTER_ARCHIVE", "true").strip().lower()
        not in {"0", "false", "no"},
        "enabled": os.getenv("AMX_RETENTION_ENABLED", "true").strip().lower() not in {"0", "false", "no"},
        "updated_at": None,
    }


class RetentionStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        if not self.path.exists():
            return default_policy()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default_policy()
        policy = default_policy()
        policy.update({k: v for k, v in data.items() if v is not None})
        return policy

    def save(self, payload: dict) -> dict:
        policy = default_policy()
        if isinstance(payload, dict):
            if "ttl_days" in payload:
                ttl = int(payload["ttl_days"])
                if ttl < 1 or ttl > 3650:
                    raise ValueError("ttl_days must be 1–3650")
                policy["ttl_days"] = ttl
            for key in ("archive_bucket", "archive_prefix"):
                if payload.get(key):
                    policy[key] = str(payload[key]).strip()
            for key in ("legal_hold_default", "delete_after_archive", "enabled"):
                if key in payload:
                    policy[key] = bool(payload[key])
        policy["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
        return policy


def _is_legal_hold(meta: dict | None, path: Path | None = None) -> bool:
    if isinstance(meta, dict) and meta.get("legal_hold"):
        return True
    if path is not None:
        sidecar = path.with_suffix(path.suffix + ".json") if path.suffix else path.with_name(path.name + ".json")
        if not sidecar.exists() and path.suffix:
            sidecar = path.with_suffix(".json")
        if sidecar.exists():
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
                if data.get("legal_hold"):
                    return True
            except (OSError, json.JSONDecodeError):
                pass
    return False


def apply_local_retention(*, root: Path, policy: dict, now: datetime | None = None) -> dict:
    """Move/delete expired local capture files. Used when MinIO is off and in tests."""
    now = now or datetime.now(timezone.utc)
    ttl = timedelta(days=int(policy.get("ttl_days") or DEFAULT_TTL_DAYS))
    archive_root = root / "archive" / str(policy.get("archive_prefix") or "eol/").strip("/")
    scanned = archived = deleted = held = skipped = 0
    errors: list[str] = []
    if not root.exists():
        return {
            "scanned": 0,
            "archived": 0,
            "deleted": 0,
            "legal_hold": 0,
            "skipped": 0,
            "errors": [],
        }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".raw", ".json"}:
            continue
        if "archive" in path.parts:
            continue
        scanned += 1
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError as exc:
            errors.append(str(exc))
            continue
        if now - mtime < ttl:
            skipped += 1
            continue
        meta = None
        if path.suffix == ".json":
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = None
        if _is_legal_hold(meta, path):
            held += 1
            continue
        rel = path.relative_to(root)
        dest = archive_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        archived += 1
        if policy.get("delete_after_archive", True):
            path.unlink(missing_ok=True)
            deleted += 1
    return {
        "scanned": scanned,
        "archived": archived,
        "deleted": deleted,
        "legal_hold": held,
        "skipped": skipped,
        "errors": errors,
        "ran_at": now.isoformat(),
    }


def apply_minio_retention(policy: dict, now: datetime | None = None) -> dict:
    from .storage_minio import apply_object_retention

    return apply_object_retention(policy, now=now)
