from __future__ import annotations

import os
from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..contracts.envelope import success_envelope
from ..production import is_production

router = APIRouter()


def app_version() -> str:
    env_ver = os.getenv("ANOMALYMATRIX_VERSION", "").strip()
    if env_ver:
        return env_ver
    for candidate in (
        Path(__file__).resolve().parents[3] / "VERSION",
        Path("/app/VERSION"),
    ):
        try:
            if candidate.exists():
                return candidate.read_text(encoding="utf-8").strip() or "1.1.0"
        except OSError:
            continue
    return "1.1.0"


def _check_postgres() -> dict:
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        return {"ok": True, "skipped": True, "detail": "DATABASE_URL unset (JSONL mode)"}
    try:
        import psycopg2

        conn = psycopg2.connect(dsn, connect_timeout=2)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "detail": str(exc.__class__.__name__)}


def _check_http(name: str, url: str, *, required: bool) -> dict:
    if not url:
        return {"ok": not required, "skipped": True, "detail": f"{name} URL unset"}
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(url)
            if response.status_code < 500:
                return {"ok": True, "status_code": response.status_code}
            return {"ok": False, "status_code": response.status_code}
    except Exception as exc:
        return {"ok": False, "detail": str(exc.__class__.__name__)}


def readiness_payload() -> tuple[dict, bool]:
    edge = os.getenv("EDGE_ACQUISITION_URL", "").strip().rstrip("/")
    gateway = os.getenv("OPCUA_GATEWAY_URL", "").strip().rstrip("/")
    checks = {
        "postgres": _check_postgres(),
        "edge": _check_http("edge", f"{edge}/health" if edge else "", required=is_production()),
        "opcua_gateway": _check_http(
            "opcua_gateway",
            f"{gateway}/health" if gateway else "",
            required=False,
        ),
    }
    ready = all(bool(item.get("ok")) for item in checks.values())
    payload = {
        "service": "anomalymatrix-api",
        "status": "ready" if ready else "not_ready",
        "version": app_version(),
        "checks": checks,
    }
    return payload, ready


@router.get("/health")
async def health(request: Request) -> dict:
    """Liveness — process is up (no dependency checks)."""
    request_id = request.state.request_id
    return success_envelope(
        {
            "service": "anomalymatrix-api",
            "status": "ok",
            "version": app_version(),
        },
        request_id,
    )


@router.get("/ready")
async def ready(request: Request):
    """Readiness — dependencies required for inspections."""
    request_id = request.state.request_id
    payload, is_ready = readiness_payload()
    body = success_envelope(payload, request_id)
    if not is_ready:
        return JSONResponse(status_code=503, content=body)
    return body
