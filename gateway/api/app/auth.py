"""Authentication and Session Management for Gateway Administrators.

Uses standard PBKDF2-SHA256 for password hashing (no compiled bcrypt/argon2 needed,
excellent for instant cross-platform self-hosting) and HS256 JWTs for session tokens.
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session, select

from .database import DB_DIR, get_session
from .models import User

# Load or generate a persistent symmetric secret key for signing session tokens
SECRET_FILE = os.path.join(DB_DIR, "gateway_secret.txt")
if os.path.exists(SECRET_FILE):
    with open(SECRET_FILE, "r") as f:
        SESSION_SECRET = f.read().strip()
else:
    SESSION_SECRET = secrets.token_urlsafe(64)
    with open(SECRET_FILE, "w") as f:
        f.write(SESSION_SECRET)

ALGORITHM = "HS256"
SESSION_DURATION_HOURS = 24


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = secrets.token_bytes(16)
    rounds = 100_000
    db_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    # Store rounds, salt, and hash combined
    return f"pbkdf2_sha256${rounds}${salt.hex()}${db_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password matches the hashed password."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        rounds = int(parts[1])
        salt = bytes.fromhex(parts[2])
        original_hash = bytes.fromhex(parts[3])
        new_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, rounds)
        return secrets.compare_digest(original_hash, new_hash)
    except Exception:
        return False


def bootstrap_admin_user(session: Session) -> str | None:
    """Ensure at least one admin user exists on boot.

    If none exist, creates user 'admin' with a random secure password and returns it
    (to be logged to the server terminal exactly once).
    """
    if session.exec(select(User)).first() is not None:
        return None
    raw_pwd = secrets.token_urlsafe(12)
    admin = User(username="admin", password_hash=hash_password(raw_pwd))
    session.add(admin)
    session.commit()
    return raw_pwd


def create_session_token(username: str) -> str:
    """Generate a JWT session token for the user."""
    expire = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)
    payload = {
        "iss": "Sjursen Digital Gateway",
        "sub": username,
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    """Dependency to retrieve the logged-in user from the Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please login again.",
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM], issuer="Sjursen Digital Gateway")
        username: str = payload.get("sub", "")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token.",
            )
        user = session.exec(select(User).where(User.username == username, User.is_active == True)).first()  # noqa: E712
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or suspended.",
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please login again.",
        )
