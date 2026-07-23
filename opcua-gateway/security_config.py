from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def enforce_production_opcua() -> None:
    if os.getenv("ANOMALYMATRIX_ENV", "dev").strip().lower() in {"prod", "production"}:
        os.environ.setdefault("OPCUA_SECURITY_ENABLED", "true")


def security_enabled() -> bool:
    enforce_production_opcua()
    return os.getenv("OPCUA_SECURITY_ENABLED", "false").strip().lower() in {"1", "true", "yes"}


def cert_directory() -> Path:
    return Path(os.getenv("OPCUA_CERT_DIR", Path(__file__).resolve().parent / "certs"))


def ensure_dev_certificates(cert_dir: Path) -> tuple[Path, Path]:
    """Use existing cert/key if present (customer PKI mount); otherwise generate self-signed."""
    cert_dir.mkdir(parents=True, exist_ok=True)
    # Prefer explicitly provided customer filenames, then defaults.
    cert_path = Path(os.getenv("OPCUA_SERVER_CERT", str(cert_dir / "server_cert.pem")))
    key_path = Path(os.getenv("OPCUA_SERVER_KEY", str(cert_dir / "server_key.pem")))
    if cert_path.exists() and key_path.exists():
        logger.info("Using OPC-UA certificate %s (will not overwrite)", cert_path)
        return cert_path, key_path

    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    now = datetime.datetime.now(datetime.timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "AnomalyMatrix OPC UA")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=825))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(key, hashes.SHA256())
    )
    # Only write into default cert_dir paths when generating.
    cert_path = cert_dir / "server_cert.pem"
    key_path = cert_dir / "server_key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    logger.warning(
        "Generated self-signed OPC-UA certificate in %s — replace with customer PKI for 24/7",
        cert_dir,
    )
    return cert_path, key_path


async def apply_server_security(server) -> dict:
    from asyncua import ua

    if not security_enabled():
        return {"enabled": False, "mode": "None"}

    cert_dir = cert_directory()
    cert_path, key_path = ensure_dev_certificates(cert_dir)
    await server.load_certificate(str(cert_path))
    await server.load_private_key(str(key_path))
    server.set_security_policy(
        [
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
        ]
    )
    server.set_security_IDs(["Username", "Certificate"])
    return {
        "enabled": True,
        "mode": "SignAndEncrypt",
        "cert_path": str(cert_path),
        "key_path": str(key_path),
    }
