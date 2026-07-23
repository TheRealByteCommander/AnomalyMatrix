from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request

from .production import auth_required, rbac_enforced

# Permissions per BUILD_READY_SPEC (IEC 62443-oriented roles)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "operator": {
        "inspection.run",
        "inspection.read",
        "recipes.read",
        "models.read",
        "trends.read",
        "contracts.read",
        "license.read",
    },
    "qa_lead": {
        "inspection.run",
        "inspection.read",
        "feedback.submit",
        "feedback.read",
        "trends.read",
        "contracts.read",
        "license.read",
    },
    "process_engineer": {
        "inspection.run",
        "inspection.read",
        "feedback.read",
        "trends.read",
        "recipes.read",
        "models.read",
        "models.train",
        "models.promote",
        "models.rollback",
        "contracts.read",
        "license.read",
    },
    "admin": {
        "inspection.run",
        "inspection.read",
        "feedback.submit",
        "feedback.read",
        "trends.read",
        "recipes.read",
        "models.read",
        "models.train",
        "models.promote",
        "models.rollback",
        "audit.read",
        "license.admin",
        "license.read",
        "contracts.read",
    },
}


@dataclass
class AuthContext:
    user_id: str
    display_name: str
    role_id: str

    def has_permission(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role_id, set())


def _dev_headers_allowed() -> bool:
    """Dev role headers are never accepted when authentication is required."""
    return not auth_required()


def resolve_auth(request: Request, core_store) -> AuthContext:
    """Resolve user from JWT, session cookie, API key, or (dev-only) headers.

    Dev headers (`X-AMX-Role` / `X-AMX-User`) are only considered when:
    - authentication is not required (non-production), AND
    - no Authorization / session / API-key credential was presented.
    Unknown roles are always rejected (never escalated to admin).
    """
    auth_header = request.headers.get("Authorization", "").strip()
    presented_bearer = auth_header.lower().startswith("bearer ")
    if presented_bearer:
        from .auth_tokens import decode_access_token

        claims = decode_access_token(auth_header[7:].strip())
        if claims:
            role = str(claims.get("role", "operator"))
            if role not in ROLE_PERMISSIONS:
                raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
            return AuthContext(
                user_id=str(claims.get("sub", "jwt-user")),
                display_name=str(claims.get("name", claims.get("sub", "jwt-user"))),
                role_id=role,
            )
        if rbac_enforced() or auth_required():
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    session_id = request.cookies.get("amx_session", "").strip()
    if session_id:
        session = core_store.get_session(session_id)
        if session:
            user = core_store.get_user_by_id(session["user_id"])
            if user:
                role = user["role_id"]
                if role not in ROLE_PERMISSIONS:
                    raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
                return AuthContext(
                    user_id=user["user_id"],
                    display_name=user.get("display_name", user["user_id"]),
                    role_id=role,
                )
        if rbac_enforced() or auth_required():
            raise HTTPException(status_code=401, detail="Invalid session")

    api_key = request.headers.get("X-AMX-Api-Key", "").strip()
    if api_key:
        user = core_store.get_user_by_api_key(api_key)
        if user:
            role = user["role_id"]
            if role not in ROLE_PERMISSIONS:
                raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
            return AuthContext(
                user_id=user["user_id"],
                display_name=user.get("display_name", user["user_id"]),
                role_id=role,
            )
        if rbac_enforced() or auth_required():
            raise HTTPException(status_code=401, detail="Invalid API key")

    if auth_required():
        raise HTTPException(status_code=401, detail="Authentication required")

    # Credential was presented but invalid and RBAC not enforced — still deny if
    # a bearer/api-key was supplied (do not fall through to spoofable headers).
    if presented_bearer or api_key:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not _dev_headers_allowed():
        raise HTTPException(status_code=401, detail="Authentication required")

    role = request.headers.get("X-AMX-Role", "operator").strip() or "operator"
    user_id = request.headers.get("X-AMX-User", "dev-operator").strip() or "dev-operator"
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
    return AuthContext(user_id=user_id, display_name=user_id, role_id=role)


def require_permission(auth: AuthContext, permission: str) -> None:
    if not rbac_enforced():
        return
    if not auth.has_permission(permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
