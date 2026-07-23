from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

SERVICE_TOKEN_HEADER = "X-AMX-Service-Token"


def service_auth_token() -> str:
    return os.getenv("SERVICE_AUTH_TOKEN", "").strip()


def require_service_auth_or_raise(headers) -> None:
    expected = service_auth_token()
    env = os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower()
    production = env in {"prod", "production"}
    if not expected:
        if production:
            raise HTTPException(status_code=503, detail="Service auth not configured")
        return
    provided = ""
    for key, value in headers.items():
        if key.lower() == SERVICE_TOKEN_HEADER.lower():
            provided = str(value).strip()
            break
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing service token")


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/contract"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if path in self.PUBLIC_PATHS or path.endswith("/health"):
            return await call_next(request)
        # Protect publish/trigger/nodes/last — contract and health remain open for ops discovery
        try:
            require_service_auth_or_raise(request.headers)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return await call_next(request)
