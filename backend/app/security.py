"""Password hashing and JWT helpers for demo auth (not production hardening)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import Settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
_PBKDF2_ITERATIONS = 120_000


def hash_password(password: str, *, salt: str | None = None) -> str:
    """Return `pbkdf2$iterations$salt$hexdigest` (stdlib only — no paid deps)."""
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt_value}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_s, salt, expected = password_hash.split("$", 3)
        if scheme != "pbkdf2":
            return False
        iterations = int(iterations_s)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), expected)


def create_access_token(
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    role_code: str,
    email: str,
    settings: Settings,
    expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org_id": str(organization_id),
        "role": role_code,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc
