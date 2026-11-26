"""Authenticated current-user endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import User
from app.schemas.common import MeResponse
from fastapi import status

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> MeResponse:
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.organization))
        .filter(User.id == auth.user_id)
        .one_or_none()
    )
    if user is None:
        raise http_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "User not found")
    return MeResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.code,
        organization_id=user.organization_id,
        organization_name=user.organization.name,
        organization_slug=user.organization.slug,
    )
