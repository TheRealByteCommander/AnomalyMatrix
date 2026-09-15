"""Vendored Byte Commander Licensing SDK (from software-licensing-concept).

Upstream: https://github.com/TheRealByteCommander/software-licensing-concept
Contract: contracts/licensing_openapi.v1.yaml
"""

from .client import LicenseClient, LicensingApiError
from .offline import (
    AMX_OFFLINE_PUBLIC_KEY,
    DEMO_DEVICE_ID,
    OfflineLicenseError,
    load_offline_license_file,
    verify_license_grant,
    verify_offline_license_file,
)

__version__ = "1.0.0"
__all__ = [
    "AMX_OFFLINE_PUBLIC_KEY",
    "DEMO_DEVICE_ID",
    "LicenseClient",
    "LicensingApiError",
    "OfflineLicenseError",
    "load_offline_license_file",
    "verify_license_grant",
    "verify_offline_license_file",
]
