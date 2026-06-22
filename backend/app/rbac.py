from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import HTTPException, Request

# Permissions per BUILD_READY_SPEC (IEC 62443-oriented roles)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "operator": {
        "inspection.run",
        "inspection.read",
        "recipes.read",
        "models.read",
        "trends.read",
    },
    "qa_lead": {
        "inspection.run",
        "inspection.read",
        "feedback.submit",
        "feedback.read",
        "trends.read",
    },
    "process_engineer": {
        "inspection.run",
        "inspection.read",
        "feedback.read",
        "trends.read",
        "recipes.read",
        "models.read",
    },
    "admin": {
        "inspection.run",
        "inspection.read",
        "feedback.submit",
        "feedback.read",
        "trends.read",
        "recipes.read",
        "models.read",
        "audit.read",
        "license.admin",
    },
}


@dataclass
class AuthContext:
    user_id: str
    display_name: str
    role_id: str

    def has_permission(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role_id, set())


def rbac_enforced() -> bool:
    return os.getenv("RBAC_ENFORCE", "false").strip().lower() in {"1", "true", "yes"}


def resolve_auth(request: Request, core_store) -> AuthContext:
    """Resolve user from X-AMX-Api-Key or dev headers X-AMX-User / X-AMX-Role."""
    api_key = request.headers.get("X-AMX-Api-Key", "").strip()
    if api_key:
        user = core_store.get_user_by_api_key(api_key)
        if user:
            return AuthContext(
                user_id=user["user_id"],
                display_name=user.get("display_name", user["user_id"]),
                role_id=user["role_id"],
            )
        if rbac_enforced():
            raise HTTPException(status_code=401, detail="Invalid API key")

    role = request.headers.get("X-AMX-Role", "operator").strip() or "operator"
    user_id = request.headers.get("X-AMX-User", "dev-operator").strip() or "dev-operator"
    if role not in ROLE_PERMISSIONS:
        if rbac_enforced():
            raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
        role = "admin"
    return AuthContext(user_id=user_id, display_name=user_id, role_id=role)


def require_permission(auth: AuthContext, permission: str) -> None:
    if not rbac_enforced():
        return
    if not auth.has_permission(permission):
        raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
