from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Request, Response

from ..auth_tokens import create_access_token, decode_access_token
from ..contracts.envelope import success_envelope
from ..core_store import CoreStore
from ..rbac import resolve_auth

router = APIRouter(tags=["auth"])


def _store(request: Request) -> CoreStore:
    return request.app.state.core_store


@router.post("/auth/login")
async def login(request: Request, response: Response, payload: dict = Body(...)):
    user_id = str(payload.get("user_id", "")).strip()
    password = str(payload.get("password", ""))
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="user_id and password required")

    user = _store(request).authenticate_user(user_id, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user_id=user["user_id"],
        role_id=user["role_id"],
        display_name=user.get("display_name", user["user_id"]),
    )
    session = _store(request).create_session(user["user_id"])
    response.set_cookie(
            key="amx_session",
            value=session["session_id"],
            httponly=True,
            samesite="lax",
            max_age=28800,
    )

    return success_envelope(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "display_name": user.get("display_name", user["user_id"]),
                "role_id": user["role_id"],
            },
            "session_id": session["session_id"],
        },
        request.state.request_id,
    )


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("amx_session", "").strip()
    if session_id:
        _store(request).revoke_session(session_id)
    response.delete_cookie("amx_session")
    return success_envelope({"logged_out": True}, request.state.request_id)


@router.get("/auth/me")
async def me(request: Request):
    auth = resolve_auth(request, _store(request))
    token_payload = None
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        token_payload = decode_access_token(header[7:].strip())
    return success_envelope(
        {
            "user_id": auth.user_id,
            "display_name": auth.display_name,
            "role_id": auth.role_id,
            "token": token_payload,
        },
        request.state.request_id,
    )
