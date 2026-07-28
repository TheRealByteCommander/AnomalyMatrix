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
    for bucket in ("heatmaps", "raw-images", "training-artifacts", "model-binaries"):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
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


def store_raw_frame(
    *,
    inspection_id: str,
    recipe_id: str,
    image_bytes: bytes,
    camera_id: str | None = None,
) -> str | None:
    if not _minio_enabled() or not image_bytes:
        return None
    try:
        client, endpoint, secure = _minio_client()
    except ImportError:
        return None
    bucket = os.getenv("MINIO_RAW_BUCKET", "raw-images").strip()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    suffix = f"_{camera_id}" if camera_id else ""
    object_name = f"{recipe_id}/{inspection_id}{suffix}.png"
    client.put_object(bucket, object_name, io.BytesIO(image_bytes), length=len(image_bytes), content_type="image/png")
    return _public_object_url(endpoint=endpoint, secure=secure, bucket=bucket, object_name=object_name)


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
