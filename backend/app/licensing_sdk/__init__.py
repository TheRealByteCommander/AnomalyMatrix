"""Vendored Byte Commander Licensing SDK (from software-licensing-concept).

Upstream: https://github.com/TheRealByteCommander/software-licensing-concept
Contract: contracts/licensing_openapi.v1.yaml
"""

from .client import LicenseClient, LicensingApiError

__version__ = "1.0.0"
__all__ = ["LicenseClient", "LicensingApiError"]
