"""Offline licenseGrant verification for industrial AnomalyMatrix PCs.

The industrial PC never calls licadmin. Vendor issues a signed `.lic.json`
bound to the machine fingerprint; this module verifies RS256 locally with
the public key embedded in AnomalyMatrix (never the key copied into the file).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

import jwt

LICENSE_GRANT_TYPE = "licenseGrant"
OFFLINE_LICENSE_FORMAT = "licenseGrant/v1"

# Pinned RS256 public key from licadmin (software-licensing-concept PR #15).
# Do not accept a swapped publicKey from the grant file.
AMX_OFFLINE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt6FuQMKaYPBg8wCyschA
ni4O+Wt4RQj7yfcF50tL6K37YZenkuMOQeOJka4G/ojuRznBarhctG5ILBEUaWsz
8yvZ1wYnD9HJC5oI20MndMN4EkKdpuUEyBw6JI/wrkCTTxbU8I+TIkQnVnpOFsLw
6XGqh9LE+66ahacE29f09ru3AA6QS9ynbmNFRM/7PRms3xKL2/qEwoHG24i+0v9F
/BjqKBDW4uHr/VSUzzTwMy2CWoABTPA3yiRcpNVYKwylPROu7ZyfM6D+mQ2tG7wC
6MRBXiMNR4sL0BA2fLNb1BVrYvrGBMtoSc3V5KEaxPESA/TAj8FThZlK/yMscuy+
9QIDAQAB
-----END PUBLIC KEY-----
"""

# Documented sample fingerprint (NOT a production machine).
DEMO_DEVICE_FINGERPRINT_RAW = "anomalymatrix-x86_64-Linux-example-machine-id-beta"
DEMO_DEVICE_ID = "4a0cb3fce728d2f463bf21cb0445eef2c157f79330767711a1ac61cfca967151"


class OfflineLicenseError(Exception):
    """Raised when a signed offline license is missing, expired, or invalid."""


def _utc_now(now: Optional[datetime] = None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _parse_expires_at(value: Any) -> Optional[datetime]:
    if value in (None, "", 0, "null"):
        return None
    if isinstance(value, datetime):
        return _utc_now(value)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OfflineLicenseError("License grant expiresAt is not a valid timestamp") from exc
    return _utc_now(parsed)


def load_offline_license_file(source: Union[str, Path, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(source, dict):
        return source
    if isinstance(source, str):
        text = source.strip()
        if text.startswith("{"):
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise OfflineLicenseError("Unsupported offline license file format") from exc
            if not isinstance(data, dict):
                raise OfflineLicenseError("Unsupported offline license file format")
            return data
        path = Path(text)
    else:
        path = Path(source)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise OfflineLicenseError("Unsupported offline license file format") from exc
    if not isinstance(data, dict):
        raise OfflineLicenseError("Unsupported offline license file format")
    return data


def verify_license_grant(
    token: str,
    public_key: str,
    device_id: str,
    now: Optional[datetime] = None,
    *,
    expected_product_id: Optional[int] = None,
) -> dict[str, Any]:
    """Verify RS256 licenseGrant and bind it to this machine's fingerprint."""
    expected = (device_id or "").strip().lower()
    clock = _utc_now(now)
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False, "require": []},
            leeway=0,
        )
    except jwt.ExpiredSignatureError as exc:
        raise OfflineLicenseError("License grant has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise OfflineLicenseError("Invalid or tampered license grant signature") from exc

    if not isinstance(decoded, dict):
        raise OfflineLicenseError("Invalid or tampered license grant signature")

    if decoded.get("exp") is not None:
        try:
            if int(clock.timestamp()) >= int(decoded["exp"]):
                raise OfflineLicenseError("License grant has expired")
        except (TypeError, ValueError) as exc:
            raise OfflineLicenseError("License grant has expired") from exc

    expires_at = _parse_expires_at(decoded.get("expiresAt"))
    if expires_at is not None and expires_at <= clock:
        raise OfflineLicenseError("License grant has expired")

    if decoded.get("grant") != LICENSE_GRANT_TYPE or decoded.get("offline") is not True:
        raise OfflineLicenseError("Token is not a licenseGrant")

    bound = str(decoded.get("deviceId") or "").strip().lower()
    if not bound or bound != expected:
        raise OfflineLicenseError("License grant is bound to a different device")

    product_id = decoded.get("productId")
    try:
        product_id_int = int(product_id)
    except (TypeError, ValueError) as exc:
        raise OfflineLicenseError("License grant is for a different product") from exc

    if expected_product_id is not None and product_id_int != int(expected_product_id):
        raise OfflineLicenseError("License grant is for a different product")

    features = decoded.get("features") or []
    if not isinstance(features, list):
        features = []

    grace = decoded.get("offlineGraceDays")
    if grace is not None:
        try:
            grace = int(grace)
        except (TypeError, ValueError):
            grace = None

    return {
        "valid": True,
        "offline": True,
        "grant": LICENSE_GRANT_TYPE,
        "licenseKey": decoded.get("licenseKey"),
        "productId": product_id_int,
        "deviceId": bound,
        "features": [item for item in features if isinstance(item, str) and item.strip()],
        "expiresAt": decoded.get("expiresAt"),
        "offlineGraceDays": grace,
        "iat": decoded.get("iat"),
        "token": token,
    }


def verify_offline_license_file(
    source: Union[str, Path, dict[str, Any]],
    device_id: str,
    public_key: Optional[str] = None,
    now: Optional[datetime] = None,
    *,
    expected_product_id: Optional[int] = None,
) -> dict[str, Any]:
    """Load a `.lic.json` grant and verify it with the embedded (pinned) public key."""
    file_data = load_offline_license_file(source)
    if file_data.get("format") != OFFLINE_LICENSE_FORMAT or not file_data.get("token"):
        raise OfflineLicenseError("Unsupported offline license file format")

    algorithm = str(file_data.get("algorithm") or "RS256").strip().upper()
    if algorithm != "RS256":
        raise OfflineLicenseError("Unsupported offline license file format")

    key = public_key or AMX_OFFLINE_PUBLIC_KEY
    if not key:
        raise OfflineLicenseError("No public key available to verify the license grant")

    return verify_license_grant(
        str(file_data["token"]),
        key,
        device_id,
        now=now,
        expected_product_id=expected_product_id,
    )
