import hashlib
import os
import secrets

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from .database import get_session
from .models import ApiKey


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def bootstrap_admin_key(session: Session) -> str | None:
    """Ensure an admin key exists.

    - KOMFYRVAKT_ADMIN_KEY env var set: that key is guaranteed to be a valid
      wildcard admin key on EVERY startup (created, un-revoked, or upgraded
      as needed). This is the break-glass recovery path if all keys are lost.
    - Otherwise, on first startup a random admin key is generated and
      returned so it can be printed exactly once. Only hashes are stored;
      raw keys are never recoverable afterwards.
    """
    env_raw = os.environ.get("KOMFYRVAKT_ADMIN_KEY")
    if env_raw:
        key_hash = hash_key(env_raw)
        existing = session.exec(select(ApiKey).where(ApiKey.key_hash == key_hash)).first()
        if existing is None:
            session.add(ApiKey(name="env-admin", key_hash=key_hash, role="admin", namespace="*"))
        elif existing.revoked or existing.role != "admin" or existing.namespace != "*":
            existing.revoked = False
            existing.role = "admin"
            existing.namespace = "*"
            session.add(existing)
        session.commit()
        return None

    if session.exec(select(ApiKey)).first() is not None:
        return None
    raw = "kv_" + secrets.token_urlsafe(32)
    session.add(ApiKey(name="bootstrap-admin", key_hash=hash_key(raw), role="admin", namespace="*"))
    session.commit()
    return raw


def get_api_key(
    x_api_key: str = Header(default=""),
    session: Session = Depends(get_session),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key = session.exec(
        select(ApiKey).where(ApiKey.key_hash == hash_key(x_api_key), ApiKey.revoked == False)  # noqa: E712
    ).first()
    if key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


def require_admin(key: ApiKey = Depends(get_api_key)) -> ApiKey:
    if key.role != "admin":
        raise HTTPException(status_code=403, detail="Admin key required")
    return key


def require_ingest(key: ApiKey = Depends(get_api_key)) -> ApiKey:
    if key.role not in ("admin", "ingest"):
        raise HTTPException(status_code=403, detail="Ingest or admin key required")
    return key


def check_namespace(key: ApiKey, namespace: str) -> None:
    """Keys are scoped on two axes: operation (role) and namespace."""
    if key.namespace not in ("*", namespace):
        raise HTTPException(status_code=403, detail=f"Key not scoped to namespace '{namespace}'")
