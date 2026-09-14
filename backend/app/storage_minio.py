from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def _minio_enabled() -> bool:
    return bool(os.getenv("MINIO_ENDPOINT", "").strip())


def _minio_client():
    from minio import Minio

    endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
    access_key = os.getenv("MINIO_ROOT_USER", "minio").strip()
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minio123").strip()
    secure = os.getenv("MINIO_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure), endpoint, secure


def _public_object_url(*, endpoint: str, secure: bool, bucket: str, object_name: str) -> str:
    """Prefer browser-reachable base (MINIO_PUBLIC_ENDPOINT / MINIO_PUBLIC_BASE) over internal Docker DNS."""
    public_base = os.getenv("MINIO_PUBLIC_BASE", "").strip().rstrip("/")
    if public_base:
        return f"{public_base}/{bucket}/{object_name}"
    public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "").strip()
    host = public_endpoint or endpoint
    scheme = "https" if secure else "http"
    if os.getenv("MINIO_PUBLIC_SECURE", "").strip().lower() in {"1", "true", "yes"}:
        scheme = "https"
    elif os.getenv("MINIO_PUBLIC_SECURE", "").strip().lower() in {"0", "false", "no"}:
        scheme = "http"
    return f"{scheme}://{host}/{bucket}/{object_name}"


def ensure_buckets() -> bool:
    if not _minio_enabled():
        return False
    try:
        client, _, _ = _minio_client()
    except ImportError:
        return False
    archive_bucket = os.getenv("MINIO_ARCHIVE_BUCKET", "archive-images").strip() or "archive-images"
    for bucket in ("heatmaps", "raw-images", "training-artifacts", "model-binaries", archive_bucket):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    _apply_lifecycle_rules(client)
    # Heatmaps are served to the HMI via nginx /artifacts/ without MinIO credentials.
    try:
        heatmap_policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": ["arn:aws:s3:::heatmaps/*"],
                    }
                ],
            }
        )
        client.set_bucket_policy("heatmaps", heatmap_policy)
    except Exception:
        pass
    return True


def _apply_lifecycle_rules(client) -> None:
    """Optional S3 lifecycle: expire raw-images after TTL, keep archive longer."""
    try:
        from minio.commonconfig import ENABLED, Filter
        from minio.lifecycleconfig import Expiration, LifecycleConfig, Rule, Transition
    except Exception:
        return
    ttl_raw = os.getenv("AMX_RETENTION_TTL_DAYS", "").strip()
    if not ttl_raw:
        return
    try:
        ttl = int(ttl_raw)
    except ValueError:
        return
    if ttl < 1:
        return
    archive_bucket = os.getenv("MINIO_ARCHIVE_BUCKET", "archive-images").strip() or "archive-images"
    archive_after = max(1, min(ttl, ttl))
    try:
        raw_bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
        client.set_bucket_lifecycle(
            raw_bucket,
            LifecycleConfig(
                [
                    Rule(
                        ENABLED,
                        rule_filter=Filter(prefix=""),
                        rule_id="amx-raw-expire",
                        expiration=Expiration(days=ttl),
                    )
                ]
            ),
        )
        client.set_bucket_lifecycle(
            archive_bucket,
            LifecycleConfig(
                [
                    Rule(
                        ENABLED,
                        rule_filter=Filter(prefix=""),
                        rule_id="amx-archive-expire",
                        expiration=Expiration(days=max(ttl * 4, 365)),
                    )
                ]
            ),
        )
        _ = Transition  # imported for future GLACIER-style hooks
    except Exception:
        pass


def store_raw_frame(
    *,
    inspection_id: str,
    recipe_id: str,
    image_bytes: bytes,
    camera_id: str | None = None,
    epc: str | None = None,
    decision: str | None = None,
    captured_at: str | None = None,
    content_type: str = "image/png",
    ext: str = "png",
    metadata: dict | None = None,
    legal_hold: bool = False,
) -> str | None:
    if not image_bytes:
        return None
    from datetime import datetime as _dt

    from .storage_layout import object_key, station_id, write_sidecar

    captured = None
    if captured_at:
        try:
            captured = _dt.fromisoformat(str(captured_at).replace("Z", "+00:00"))
        except ValueError:
            captured = None
    object_name = object_key(
        station=station_id(),
        recipe_id=recipe_id,
        epc=epc or "unbound",
        camera_id=camera_id or "cam",
        captured_at=captured,
        decision=decision or "pending",
        ext=ext,
        kind="image",
    )
    if not _minio_enabled():
        return None
    try:
        client, endpoint, secure = _minio_client()
    except ImportError:
        return None
    bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    headers = {"inspection-id": inspection_id, "legal-hold": "true" if legal_hold else "false"}
    if epc:
        headers["epc"] = str(epc)[:128]
    client.put_object(
        bucket,
        object_name,
        io.BytesIO(image_bytes),
        length=len(image_bytes),
        content_type=content_type or "image/png",
        metadata=headers,
    )
    if metadata:
        meta_name = object_name.rsplit(".", 1)[0] + ".json"
        body = json.dumps(metadata, indent=2).encode("utf-8")
        client.put_object(bucket, meta_name, io.BytesIO(body), length=len(body), content_type="application/json")
        _ = write_sidecar
    return _public_object_url(endpoint=endpoint, secure=secure, bucket=bucket, object_name=object_name)


def store_local_capture(
    *,
    data_root: Path,
    inspection_id: str,
    recipe_id: str,
    image_bytes: bytes,
    camera_id: str | None = None,
    epc: str | None = None,
    decision: str | None = None,
    captured_at: str | None = None,
    ext: str = "png",
    metadata: dict | None = None,
) -> str | None:
    if not image_bytes:
        return None
    from datetime import datetime as _dt

    from .storage_layout import object_key, station_id, write_sidecar

    captured = None
    if captured_at:
        try:
            captured = _dt.fromisoformat(str(captured_at).replace("Z", "+00:00"))
        except ValueError:
            captured = None
    object_name = object_key(
        station=station_id(),
        recipe_id=recipe_id,
        epc=epc or "unbound",
        camera_id=camera_id or "cam",
        captured_at=captured,
        decision=decision or "pending",
        ext=ext,
        kind="image",
    )
    path = Path(data_root) / "captures" / object_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    if metadata:
        write_sidecar(path.with_suffix(".json"), metadata)
    return str(path)


def storage_stats(*, data_root: Path | None = None) -> dict:
    """Bytes / count / avg size for MinIO raw-images and local captures."""
    formats: dict[str, int] = {}
    colorspaces: dict[str, int] = {}
    total_bytes = 0
    count = 0
    source = "none"

    if _minio_enabled():
        try:
            client, _, _ = _minio_client()
            bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
            if client.bucket_exists(bucket):
                source = "minio"
                for obj in client.list_objects(bucket, recursive=True):
                    name = obj.object_name or ""
                    if name.endswith(".json"):
                        continue
                    size = int(getattr(obj, "size", 0) or 0)
                    total_bytes += size
                    count += 1
                    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "bin"
                    formats[ext] = formats.get(ext, 0) + 1
        except Exception:
            pass

    if data_root is not None:
        captures = Path(data_root) / "captures"
        if captures.exists():
            if source == "none":
                source = "local"
            elif source == "minio":
                source = "minio+local"
            for path in captures.rglob("*"):
                if not path.is_file() or path.suffix.lower() == ".json":
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                total_bytes += size
                count += 1
                ext = path.suffix.lower().lstrip(".") or "bin"
                formats[ext] = formats.get(ext, 0) + 1
                sidecar = path.with_suffix(".json")
                if sidecar.exists():
                    try:
                        meta = json.loads(sidecar.read_text(encoding="utf-8"))
                        cs = str(meta.get("colorspace") or "").lower()
                        if cs:
                            colorspaces[cs] = colorspaces.get(cs, 0) + 1
                    except (OSError, json.JSONDecodeError):
                        pass

    avg = int(total_bytes / count) if count else 0
    return {
        "object_count": count,
        "total_bytes": total_bytes,
        "avg_bytes": avg,
        "formats": formats,
        "colorspaces": colorspaces,
        "source": source,
        "bucket": os.getenv("MINIO_RAW_BUCKET", "raw-images"),
    }


def apply_object_retention(policy: dict, now: datetime | None = None) -> dict:
    """Archive then optionally delete MinIO objects older than TTL (skip legal hold)."""
    now = now or datetime.now(timezone.utc)
    scanned = archived = deleted = held = skipped = 0
    errors: list[str] = []
    if not _minio_enabled() or not policy.get("enabled", True):
        return {
            "scanned": 0,
            "archived": 0,
            "deleted": 0,
            "legal_hold": 0,
            "skipped": 0,
            "errors": [],
            "backend": "minio-disabled",
            "ran_at": now.isoformat(),
        }
    try:
        client, _, _ = _minio_client()
    except ImportError:
        return {
            "scanned": 0,
            "archived": 0,
            "deleted": 0,
            "legal_hold": 0,
            "skipped": 0,
            "errors": ["minio missing"],
            "backend": "minio",
            "ran_at": now.isoformat(),
        }
    bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
    archive_bucket = str(policy.get("archive_bucket") or "archive-images")
    prefix = str(policy.get("archive_prefix") or "eol/")
    ttl_days = int(policy.get("ttl_days") or 90)
    if not client.bucket_exists(bucket):
        return {
            "scanned": 0,
            "archived": 0,
            "deleted": 0,
            "legal_hold": 0,
            "skipped": 0,
            "errors": [],
            "backend": "minio",
            "ran_at": now.isoformat(),
        }
    if not client.bucket_exists(archive_bucket):
        client.make_bucket(archive_bucket)
    cutoff = now.timestamp() - ttl_days * 86400
    for obj in client.list_objects(bucket, recursive=True):
        scanned += 1
        last_mod = getattr(obj, "last_modified", None)
        try:
            ts = last_mod.timestamp() if last_mod is not None else 0
        except Exception:
            ts = 0
        if ts and ts > cutoff:
            skipped += 1
            continue
        meta = {}
        try:
            info = client.stat_object(bucket, obj.object_name)
            meta = dict(getattr(info, "metadata", None) or {})
        except Exception:
            meta = {}
        hold = str(meta.get("legal-hold") or meta.get("X-Amz-Meta-Legal-Hold") or "").lower() in {
            "true",
            "1",
            "yes",
        }
        if hold:
            held += 1
            continue
        dest = f"{prefix.rstrip('/')}/{obj.object_name}"
        try:
            try:
                from minio.commonconfig import CopySource

                client.copy_object(archive_bucket, dest, CopySource(bucket, obj.object_name))
            except Exception:
                client.copy_object(archive_bucket, dest, f"{bucket}/{obj.object_name}")
            archived += 1
            if policy.get("delete_after_archive", True):
                client.remove_object(bucket, obj.object_name)
                deleted += 1
        except Exception as exc:
            errors.append(f"{obj.object_name}:{exc.__class__.__name__}")
    return {
        "scanned": scanned,
        "archived": archived,
        "deleted": deleted,
        "legal_hold": held,
        "skipped": skipped,
        "errors": errors[:20],
        "backend": "minio",
        "ran_at": now.isoformat(),
    }


def store_heatmap_binary(
    *,
    inspection_id: str,
    png_bytes: bytes,
    anomaly_score: float,
    camera_id: str | None = None,
) -> str | None:
    if not _minio_enabled() or not png_bytes:
        return store_heatmap_artifact(inspection_id=inspection_id, heatmap_uri="", anomaly_score=anomaly_score)
    try:
        client, endpoint, secure = _minio_client()
    except ImportError:
        return None
    bucket = os.getenv("MINIO_HEATMAP_BUCKET", "heatmaps").strip()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    view = camera_id or "primary"
    object_name = f"{inspection_id}/{view}/overlay.png"
    client.put_object(bucket, object_name, io.BytesIO(png_bytes), length=len(png_bytes), content_type="image/png")
    meta_name = f"{inspection_id}/{view}/metadata.json"
    meta = json.dumps(
        {
            "inspection_id": inspection_id,
            "camera_id": camera_id,
            "anomaly_score": anomaly_score,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "overlay": object_name,
        }
    ).encode("utf-8")
    client.put_object(bucket, meta_name, io.BytesIO(meta), length=len(meta), content_type="application/json")
    return _public_object_url(endpoint=endpoint, secure=secure, bucket=bucket, object_name=object_name)


def store_heatmap_artifact(*, inspection_id: str, heatmap_uri: str, anomaly_score: float) -> str | None:
    if not _minio_enabled():
        return None
    try:
        client, endpoint, secure = _minio_client()
    except ImportError:
        return None
    bucket = os.getenv("MINIO_HEATMAP_BUCKET", "heatmaps").strip()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    object_name = f"{inspection_id}/metadata.json"
    body = json.dumps(
        {
            "inspection_id": inspection_id,
            "source_uri": heatmap_uri,
            "anomaly_score": anomaly_score,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        },
        indent=2,
    ).encode("utf-8")
    client.put_object(bucket, object_name, io.BytesIO(body), length=len(body), content_type="application/json")
    return _public_object_url(endpoint=endpoint, secure=secure, bucket=bucket, object_name=object_name)


def list_training_image_bytes(*, recipe_id: str, limit: int = 64) -> list[bytes]:
    images: list[bytes] = []
    if _minio_enabled():
        try:
            import cv2

            client, _, _ = _minio_client()
            bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
            prefix = f"{recipe_id}/"
            for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
                if not obj.object_name.endswith(".png"):
                    continue
                response = client.get_object(bucket, obj.object_name)
                data = response.read()
                response.close()
                response.release_conn()
                images.append(data)
                if len(images) >= limit:
                    break
        except Exception:
            pass
    return images


def load_local_training_images(data_root: Path, recipe_id: str, *, limit: int = 64) -> list[np.ndarray]:
    import cv2

    folder = data_root / "training-images" / recipe_id
    images: list[np.ndarray] = []
    if not folder.exists():
        return images
    for path in sorted(folder.glob("*.png"))[:limit]:
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images.append(img)
    return images


def decode_png_bytes(data: bytes) -> np.ndarray | None:
    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        return None
