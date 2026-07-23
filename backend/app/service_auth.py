from __future__ import annotations

import os
import secrets
from typing import Mapping

from fastapi import HTTPException, Request

from .production import is_production


SERVICE_TOKEN_HEADER = "X-AMX-Service-Token"


def service_auth_token() -> str:
    return os.getenv("SERVICE_AUTH_TOKEN", "").strip()


def service_auth_headers() -> dict[str, str]:
    token = service_auth_token()
    if not token:
        return {}
    return {SERVICE_TOKEN_HEADER: token}


def require_service_auth(request: Request) -> None:
    """Enforce shared service token when configured (always in production)."""
    expected = service_auth_token()
    if not expected:
        if is_production():
            raise HTTPException(status_code=503, detail="Service auth not configured")
        return
    provided = request.headers.get(SERVICE_TOKEN_HEADER, "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing service token")


def extract_service_token(headers: Mapping[str, str] | None) -> str:
    if not headers:
        return ""
    for key, value in headers.items():
        if key.lower() == SERVICE_TOKEN_HEADER.lower():
            return str(value).strip()
    return ""
