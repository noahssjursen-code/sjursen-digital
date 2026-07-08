"""Asymmetric cryptographic licensing system for Sjursen Digital.

Uses RSA signature verification (RS256) to validate license keys completely offline.
The public key is hardcoded here; the private key (stored in tools/generate_license.py)
is used to issue licenses.

For developers: If SD_DEV_MODE=1 is set, licensing checks are bypassed and all
modules are fully unlocked.
"""
import os
from datetime import datetime
from typing import Optional

import jwt
from pydantic import BaseModel

# Hardcoded Sjursen Digital RSA Public Key (PEM format)
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzA+KdvObDfbRSowL2nSD
GbcJbHKn0Q/9uG+sKHDEeYYitE34op+gFWIytqpIg19FcG8+c7WikZSSkfpsr8eR
EjHfhMNJbdrUt8n//ZbYGS4mIkYBCofTah9J/IxIpJLO/nAVSy4Qp8IEjt0Xwh3g
Lgwp9Zzv4KcQsu1UcYqLsV8Gl9A21K+Ko4GqZ1xJILLwBELCAnhBdXoC6JAwdgZE
k54zCGQB80Tym8sNaBhswGdcz/hYP63VIA9wIVOW3yOKGoeC9AsHXXLUgAfgebhf
VteaOrGSeHpefUBIjJ+CSVkZL+RI4e5XlKPf3i50Qj0f9f+++oWMojLX9AwSwF1N
FQIDAQAB
-----END PUBLIC KEY-----"""


class LicensePayload(BaseModel):
    customer_name: str
    customer_email: str
    modules: dict[str, bool]
    expires_at: Optional[datetime] = None


def is_dev_mode() -> bool:
    return os.environ.get("SD_DEV_MODE", "0") in ("1", "true", "True")


def get_mock_payload() -> dict:
    return {
        "customer_name": "Developer Noah",
        "customer_email": "noah@sjursen.digital",
        "modules": {
            "komfyrvakt": True,
            "obsero": True,
            "future_app": True,
        },
        "expires_at": None,
    }


def verify_license(license_key: str) -> Optional[dict]:
    """Verify an RS256-signed JWT license key.

    Returns the decoded payload dict if valid, or None if invalid/expired.
    """
    if is_dev_mode():
        return get_mock_payload()

    if not license_key:
        return None

    try:
        # RS256 ensures the token was signed with our private key and hasn't been tampered with.
        payload = jwt.decode(
            license_key.strip(),
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="Sjursen Digital",
        )
        expires_at = None
        if "exp" in payload:
            expires_at = datetime.utcfromtimestamp(payload["exp"])

        return {
            "customer_name": payload.get("sub", "Valued Customer"),
            "customer_email": payload.get("email", ""),
            "modules": payload.get("modules", {}),
            "expires_at": expires_at,
        }
    except jwt.PyJWTError:
        return None


def is_module_licensed(license_payload: Optional[dict], module_name: str) -> bool:
    """Check if a specific module is licensed and enabled."""
    if is_dev_mode():
        return True
    if not license_payload:
        return False
    # Check expiry
    expires_at = license_payload.get("expires_at")
    if expires_at and expires_at < datetime.utcnow():
        return False
    return bool(license_payload.get("modules", {}).get(module_name))
