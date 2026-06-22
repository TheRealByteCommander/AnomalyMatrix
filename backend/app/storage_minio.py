from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone


def _minio_enabled() -> bool:
    return bool(os.getenv("MINIO_ENDPOINT", "").strip())


def ensure_buckets() -> bool:
    if not _minio_enabled():
        return False
    try:
        from minio import Minio
    except ImportError:
        return False

    endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
    access_key = os.getenv("MINIO_ROOT_USER", "minio").strip()
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minio123").strip()
    secure = os.getenv("MINIO_SECURE", "false").strip().lower() in {"1", "true", "yes"}

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    for bucket in ("heatmaps", "raw-images", "training-artifacts"):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    return True


def store_heatmap_artifact(*, inspection_id: str, heatmap_uri: str, anomaly_score: float) -> str | None:
    """Store heatmap metadata JSON in MinIO; returns object URI or None if disabled."""
    if not _minio_enabled():
        return None

    try:
        from minio import Minio
    except ImportError:
        return None

    endpoint = os.getenv("MINIO_ENDPOINT", "").strip()
    access_key = os.getenv("MINIO_ROOT_USER", "minio").strip()
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minio123").strip()
    secure = os.getenv("MINIO_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    bucket = os.getenv("MINIO_HEATMAP_BUCKET", "heatmaps").strip()

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    object_name = f"{inspection_id}/metadata.json"
    body = json.dumps(
        {
            "inspection_id": inspection_id,
            "source_uri": heatmap_uri,
            "anomaly_score": anomaly_score,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "note": "MVP metadata placeholder; binary heatmap overlay follows in model integration phase.",
        },
        indent=2,
    ).encode("utf-8")

    client.put_object(
        bucket,
        object_name,
        io.BytesIO(body),
        length=len(body),
        content_type="application/json",
    )
    scheme = "https" if secure else "http"
    return f"{scheme}://{endpoint}/{bucket}/{object_name}"
