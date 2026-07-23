from __future__ import annotations

import os
import sys


_DEFAULT_SECRETS = {
    "changeme",
    "change-me-in-production",
    "anomaly_pw",
    "minio123",
    "anomaly-token",
    "amx-key-operator",
    "amx-key-qa",
    "amx-key-engineer",
    "amx-key-admin",
    "dev-jwt-secret-change-me-in-production-min-32b",
}


def is_production() -> bool:
    return os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() in {"prod", "production"}


def auth_required() -> bool:
    """Require JWT/session/API key — dev headers are never accepted when true."""
    return is_production()


def rbac_enforced() -> bool:
    """Enforce role permissions (dev headers allowed outside production)."""
    if is_production():
        return True
    return os.getenv("RBAC_ENFORCE", "false").strip().lower() in {"1", "true", "yes"}


def cookie_secure() -> bool:
    if os.getenv("COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes"}:
        return True
    if os.getenv("COOKIE_SECURE", "").strip().lower() in {"0", "false", "no"}:
        return False
    return is_production()


def validate_production_config() -> list[str]:
    if not is_production():
        return []

    errors: list[str] = []
    required = {
        "JWT_SECRET": "JWT signing secret",
        "DATABASE_URL": "Postgres DSN",
        "LICENSE_ADMIN_TOKEN": "License admin token",
        "AMX_CORS_ORIGINS": "Allowed HMI origins (comma-separated)",
        "SERVICE_AUTH_TOKEN": "Inter-service auth token (edge/OPC-UA)",
    }
    for key, label in required.items():
        if not os.getenv(key, "").strip():
            errors.append(f"Missing {label} ({key})")

    jwt = os.getenv("JWT_SECRET", "")
    if jwt and len(jwt) < 32:
        errors.append("JWT_SECRET must be at least 32 characters")

    service_token = os.getenv("SERVICE_AUTH_TOKEN", "")
    if service_token and len(service_token) < 24:
        errors.append("SERVICE_AUTH_TOKEN must be at least 24 characters")

    if os.getenv("RBAC_ENFORCE", "false").strip().lower() not in {"1", "true", "yes"}:
        errors.append("RBAC_ENFORCE must be true in production")

    if os.getenv("LICENSE_ENFORCE", "false").strip().lower() not in {"1", "true", "yes"}:
        errors.append("LICENSE_ENFORCE must be true in production")

    if os.getenv("ANOMALYMATRIX_INFERENCE_PROVIDER", "stub").strip().lower() == "stub":
        errors.append("ANOMALYMATRIX_INFERENCE_PROVIDER must not be 'stub' in production")

    if is_production() and os.getenv("OPCUA_SECURITY_ENABLED", "false").strip().lower() not in {"1", "true", "yes"}:
        errors.append("OPCUA_SECURITY_ENABLED must be true in production")

    if is_production() and not os.getenv("EDGE_ACQUISITION_URL", "").strip():
        errors.append("EDGE_ACQUISITION_URL must be set in production")

    if is_production() and not os.getenv("OPCUA_API_KEY", "").strip():
        errors.append("OPCUA_API_KEY must be set in production")

    for key in (
        "JWT_SECRET",
        "POSTGRES_PASSWORD",
        "MINIO_ROOT_PASSWORD",
        "LICENSE_ADMIN_TOKEN",
        "SERVICE_AUTH_TOKEN",
        "OPCUA_API_KEY",
        "INFLUX_TOKEN",
    ):
        val = os.getenv(key, "")
        if val in _DEFAULT_SECRETS:
            errors.append(f"{key} uses a default/dev value — rotate for production")

    return errors


def enforce_production_config() -> None:
    errors = validate_production_config()
    if errors:
        for err in errors:
            print(f"[AnomalyMatrix][FATAL] {err}", file=sys.stderr)
        raise SystemExit(1)
