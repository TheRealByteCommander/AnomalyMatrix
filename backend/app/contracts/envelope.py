from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_envelope(data: Any, request_id: str) -> dict[str, Any]:
    return {
        "ok": True,
        "data": data,
        "meta": {
            "requestId": request_id,
            "timestamp": utc_now_iso(),
        },
    }


def error_envelope(
    code: str,
    message: str,
    request_id: str,
    *,
    details: Any = None,
    retryable: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "retryable": retryable,
        },
        "meta": {
            "requestId": request_id,
            "timestamp": utc_now_iso(),
        },
    }
