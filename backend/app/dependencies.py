"""FastAPI dependencies — demo JWT auth with organization scoping."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from fastapi import status
from sqlalchemy.orm import Session, joinedload

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.config import Settings, get_settings
from app.db.session import get_db
from app.errors import http_error
from app.models import User
from app.security import decode_access_token


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    email: str
    display_name: str


def get_current_settings() -> Settings:
    return get_settings()


def get_provider() -> AIProvider:
    return get_ai_provider()


async def get_auth_context(
    authorization: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_current_settings),
    db: Session = Depends(get_db),
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "unauthorized",
            "Missing Bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise http_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "Missing Bearer token")

    try:
        payload = decode_access_token(token, settings)
        user_id = uuid.UUID(str(payload["sub"]))
        org_id = uuid.UUID(str(payload["org_id"]))
    except (ValueError, KeyError, TypeError):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_token",
            "Invalid or expired access token",
        ) from None

    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.organization))
        .filter(User.id == user_id, User.is_active.is_(True))
        .one_or_none()
    )
    if user is None:
        raise http_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "User not found or inactive")
    if user.organization_id != org_id:
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_token",
            "Token organization does not match user",
        )

    return AuthContext(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.code,
        email=user.email,
        display_name=user.display_name,
    )


def require_organization(organization_id: uuid.UUID, auth: AuthContext) -> None:
    """Enforce that the caller may only access their own organization."""
    if auth.organization_id != organization_id:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "forbidden_organization",
            "Access to this organization is denied",
            {"requested_organization_id": str(organization_id)},
        )


# Backwards-compatible alias used by scaffold AI routes if imported elsewhere
async def require_demo_token(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    return auth
