import sys
from pathlib import Path

GW_ROOT = Path(__file__).resolve().parents[2] / "opcua-gateway"
sys.path.insert(0, str(GW_ROOT))

from security_config import cert_directory, ensure_dev_certificates, security_enabled  # noqa: E402


def test_opcua_security_profile_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("OPCUA_SECURITY_ENABLED", "true")
    monkeypatch.setenv("OPCUA_CERT_DIR", str(tmp_path / "certs"))
    assert security_enabled() is True
    cert_path, key_path = ensure_dev_certificates(cert_directory())
    assert cert_path.exists()
    assert key_path.exists()
