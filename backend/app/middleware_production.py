from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .production import is_production

logger = logging.getLogger("anomalymatrix.api")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-Id") or str(uuid4())
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
        log_entry = {
            "level": "info",
            "msg": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
  def __init__(self, app, *, limit: int = 120, window_sec: int = 60):
    super().__init__(app)
    self.limit = limit
    self.window_sec = window_sec
    self._hits: dict[str, list[float]] = defaultdict(list)
    self._lock = Lock()

  async def dispatch(self, request: Request, call_next):
    if request.url.path.endswith("/health"):
      return await call_next(request)

    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    now = time.time()
    with self._lock:
      window = [t for t in self._hits[key] if now - t < self.window_sec]
      if len(window) >= self.limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
      window.append(now)
      self._hits[key] = window
    return await call_next(request)


def configure_cors(app) -> None:
    raw = os.getenv("AMX_CORS_ORIGINS", os.getenv("BC_CORS_ORIGINS", "")).strip()
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
    elif is_production():
        origins = []
    else:
        origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


def configure_production_middleware(app) -> None:
    configure_cors(app)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
