from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)


def run_inspection_sync(*, camera_id: str | None = None, recipe_id: str | None = None) -> dict | None:
    base = os.getenv("ANOMALYMATRIX_API_URL", "http://127.0.0.1:8080").rstrip("/")
    api_key = os.getenv("OPCUA_API_KEY", "").strip()
    if not api_key and os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() not in {"prod", "production"}:
        api_key = "amx-key-operator"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-AMX-Api-Key"] = api_key
    body = {
        "camera_id": camera_id or os.getenv("OPCUA_DEFAULT_CAMERA_ID", "cam-01"),
        "recipe_id": recipe_id or os.getenv("OPCUA_DEFAULT_RECIPE_ID", "recipe-default"),
    }
    try:
        with httpx.Client(timeout=float(os.getenv("OPCUA_INSPECTION_TIMEOUT_SEC", "30"))) as client:
            response = client.post(f"{base}/api/v1/inspections/run", json=body, headers=headers)
            response.raise_for_status()
            envelope = response.json()
            if envelope.get("ok") and envelope.get("data"):
                return envelope["data"]
            logger.warning("Inspection API returned not ok: %s", envelope)
    except Exception as exc:
        logger.exception("Inspection API call failed: %s", exc)
    return None
