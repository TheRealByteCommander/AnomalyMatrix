from __future__ import annotations

import hashlib
import os
import secrets
import time
from typing import Any

import jwt

JWT_ALG = "HS256"
JWT_EXPIRE_SEC = int(os.getenv("JWT_EXPIRE_SEC", "28800"))


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return secret
    if os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() == "prod":
        raise RuntimeError("JWT_SECRET must be set in production")
    return "dev-jwt-secret-change-me-in-production-min-32b"


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return secrets.compare_digest(actual, expected)


def create_access_token(*, user_id: str, role_id: str, display_name: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role_id,
        "name": display_name,
        "iat": now,
        "exp": now + JWT_EXPIRE_SEC,
        "typ": "access",
    }
    return jwt.encode(payload, jwt_secret(), algorithm=JWT_ALG)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


def create_session_id() -> str:
    return secrets.token_urlsafe(32)
