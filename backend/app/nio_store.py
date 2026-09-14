from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .storage_minio import store_raw_frame


_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def safe_id(value: str | None, *, fallback: str = "unknown") -> str:
    cleaned = _SAFE_ID.sub("", str(value or "").strip())
    return cleaned or fallback


def nio_images_dir(data_root: Path, recipe_id: str) -> Path:
    return Path(data_root) / "nio-images" / safe_id(recipe_id, fallback="recipe-default")


def inspection_frames_dir(data_root: Path, inspection_id: str) -> Path:
    return Path(data_root) / "inspection-frames" / safe_id(inspection_id)


def count_nio_images(data_root: Path, recipe_id: str) -> int:
    folder = nio_images_dir(data_root, recipe_id)
    if not folder.exists():
        return 0
    active = 0
    for path in folder.glob("*.png"):
        meta = _read_meta(path.with_suffix(".json"))
        if meta.get("active", True):
            active += 1
    return active


def save_inspection_frame_png(
    *,
    data_root: Path,
    inspection_id: str,
    camera_id: str,
    png_bytes: bytes,
) -> str | None:
    if not png_bytes:
        return None
    folder = inspection_frames_dir(data_root, inspection_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_id(camera_id, fallback='cam')}.png"
    path.write_bytes(png_bytes)
    return str(path)


def png_bytes_from_frame(frame: dict | None, *, data_root: Path | None = None) -> bytes | None:
    payload = frame or {}
    b64 = payload.get("image_b64")
    if b64:
        try:
            raw = base64.b64decode(b64)
        except Exception:
            raw = b""
        encoded = _ensure_png(raw)
        if encoded:
            return encoded
    for key in ("local_png_path", "stored_raw_uri", "image_uri"):
        uri = str(payload.get(key) or "")
        local = _local_path_from_uri(uri, data_root=data_root)
        if local and local.exists():
            encoded = _ensure_png(local.read_bytes())
            if encoded:
                return encoded
    return None


def persist_nio_sample(
    *,
    data_root: Path,
    inspection: dict,
    feedback_id: str,
    actor: str,
) -> dict | None:
    recipe_id = str((inspection.get("frame") or {}).get("recipe_id") or "recipe-default")
    views = list(inspection.get("views") or [])
    if not views:
        views = [
            {
                "camera_id": (inspection.get("frame") or {}).get("camera_id") or "cam-01",
                "frame": inspection.get("frame") or {},
            }
        ]
    saved: list[str] = []
    primary: dict[str, Any] | None = None
    folder = nio_images_dir(data_root, recipe_id)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    for view in views:
        camera_id = str(view.get("camera_id") or (view.get("frame") or {}).get("camera_id") or "cam-01")
        png_bytes = png_bytes_from_frame(view.get("frame") or inspection.get("frame"), data_root=data_root)
        if not png_bytes:
            continue
        filename = f"{safe_id(inspection.get('inspection_id'))}_{safe_id(camera_id, fallback='cam')}.png"
        path = folder / filename
        path.write_bytes(png_bytes)
        meta = {
            "inspection_id": inspection.get("inspection_id"),
            "recipe_id": recipe_id,
            "camera_id": camera_id,
            "feedback_id": feedback_id,
            "actor": actor,
            "anomaly_score": (view.get("inference") or inspection.get("inference") or {}).get("anomaly_score"),
            "active": True,
            "created_at": stamp,
            "path": str(path),
        }
        path.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        store_raw_frame(
            inspection_id=f"nio-{inspection.get('inspection_id')}",
            recipe_id=f"nio/{recipe_id}",
            image_bytes=png_bytes,
            camera_id=camera_id,
        )
        saved.append(str(path))
        if primary is None:
            primary = meta
    if not primary:
        return None
    primary["saved"] = len(saved)
    primary["paths"] = saved
    primary["count"] = count_nio_images(data_root, recipe_id)
    return primary


def retract_nio_sample(data_root: Path, inspection_id: str) -> int:
    root = Path(data_root) / "nio-images"
    if not root.exists():
        return 0
    updated = 0
    needle = safe_id(inspection_id)
    for meta_path in root.glob("*/*.json"):
        meta = _read_meta(meta_path)
        if str(meta.get("inspection_id") or "") != str(inspection_id) and needle not in meta_path.stem:
            continue
        if not meta:
            continue
        meta["active"] = False
        meta["retracted_at"] = datetime.now(timezone.utc).isoformat()
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        updated += 1
    return updated


def load_local_nio_images(data_root: Path, recipe_id: str, *, limit: int = 64) -> list[np.ndarray]:
    import cv2

    folder = nio_images_dir(data_root, recipe_id)
    images: list[np.ndarray] = []
    if not folder.exists():
        return images
    for path in sorted(folder.glob("*.png")):
        meta = _read_meta(path.with_suffix(".json"))
        if not meta.get("active", True):
            continue
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images.append(img)
        if len(images) >= limit:
            break
    return images


def _read_meta(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _local_path_from_uri(uri: str, *, data_root: Path | None = None) -> Path | None:
    if not uri:
        return None
    if uri.startswith("file://"):
        return Path(uri[7:])
    path = Path(uri)
    if path.is_absolute() and path.exists():
        return path
    if data_root and not path.is_absolute():
        candidate = Path(data_root) / path
        if candidate.exists():
            return candidate
    return None


def _ensure_png(raw: bytes) -> bytes | None:
    if not raw:
        return None
    if raw.startswith(b"\x89PNG"):
        return raw
    try:
        import cv2

        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        ok, buf = cv2.imencode(".png", img)
        return buf.tobytes() if ok else None
    except Exception:
        return None
