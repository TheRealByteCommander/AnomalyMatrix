from __future__ import annotations

from fastapi import APIRouter, Request

from ..contracts.envelope import success_envelope

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    request_id = request.state.request_id
    return success_envelope(
        {
            "service": "anomalymatrix-api",
            "status": "ok",
            "version": "1.0.0",
        },
        request_id,
    )
