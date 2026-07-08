"""Auth model, tuned for self-hosting:

- The DASHBOARD (admin/read endpoints) is open by default. Whoever can
  reach the port owns the box; forcing them to paste a key from server
  logs is hostile UX. Set KOMFYRVAKT_LOCK_DASHBOARD=1 to require an admin
  key on those endpoints (for instances exposed beyond a trusted network).
- INGEST (machines pushing logs) always requires a key. That's services
  talking to services: keys are scoped per namespace and manageable from
  the dashboard, where they can be viewed, generated, and revoked.
"""
import hashlib
import os
import secrets

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from .database import get_session
from .models import ApiKey


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def new_raw_key() -> str:
    return "kv_" + secrets.token_urlsafe(32)


def dashboard_locked() -> bool:
    return os.environ.get("KOMFYRVAKT_LOCK_DASHBOARD", "0") not in ("0", "", "false")


def bootstrap_admin_key(session: Session) -> str | None:
    """Ensure at least one admin key exists.

    - KOMFYRVAKT_ADMIN_KEY env var set: that exact key is guaranteed to be a
      valid wildcard admin key on EVERY startup (break-glass recovery path).
    - Otherwise, on first startup a random admin key is generated. It stays
      visible on the dashboard's Keys page.
    """
    env_raw = os.environ.get("KOMFYRVAKT_ADMIN_KEY")
    if env_raw:
        key_hash = hash_key(env_raw)
        existing = session.exec(select(ApiKey).where(ApiKey.key_hash == key_hash)).first()
        if existing is None:
            session.add(ApiKey(name="env-admin", key=env_raw, key_hash=key_hash, role="admin", namespace="*"))
        elif existing.revoked or existing.role != "admin" or existing.namespace != "*":
            existing.revoked = False
            existing.role = "admin"
            existing.namespace = "*"
            session.add(existing)
        session.commit()
        return None

    if session.exec(select(ApiKey)).first() is not None:
        return None
    raw = new_raw_key()
    session.add(ApiKey(name="bootstrap-admin", key=raw, key_hash=hash_key(raw), role="admin", namespace="*"))
    session.commit()
    return raw


def _lookup(session: Session, raw: str) -> ApiKey | None:
    if not raw:
        return None
    return session.exec(
        select(ApiKey).where(ApiKey.key_hash == hash_key(raw), ApiKey.revoked == False)  # noqa: E712
    ).first()


def require_admin(
    x_api_key: str = Header(default=""),
    session: Session = Depends(get_session),
) -> ApiKey:
    """Dashboard endpoints. Open unless KOMFYRVAKT_LOCK_DASHBOARD is set."""
    if not dashboard_locked():
        return ApiKey(name="open-dashboard", key_hash="", role="admin", namespace="*")
    key = _lookup(session, x_api_key)
    if key is None:
        raise HTTPException(status_code=401, detail="Dashboard is locked; valid X-API-Key required")
    if key.role != "admin":
        raise HTTPException(status_code=403, detail="Admin key required")
    return key


def require_ingest(
    x_api_key: str = Header(default=""),
    session: Session = Depends(get_session),
) -> ApiKey:
    """Ingest always requires a key - this is machine-to-machine traffic."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header (ingest requires a key)")
    key = _lookup(session, x_api_key)
    if key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


def check_namespace(key: ApiKey, namespace: str) -> None:
    """Keys are scoped on two axes: operation (role) and namespace."""
    if key.namespace not in ("*", namespace):
        raise HTTPException(status_code=403, detail=f"Key not scoped to namespace '{namespace}'")
