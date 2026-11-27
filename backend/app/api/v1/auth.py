"""Demo login against seeded users — local JWT, not production auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.db.session import get_db
from app.dependencies import get_current_settings
from app.errors import http_error
from app.models import User
from app.schemas.common import DemoLoginRequest, DemoLoginResponse
from app.security import create_access_token, verify_password
from app.services.rate_limit import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-login", response_model=DemoLoginResponse)
async def demo_login(
    body: DemoLoginRequest,
    request: Request,
    settings: Settings = Depends(get_current_settings),
    db: Session = Depends(get_db),
) -> DemoLoginResponse:
    if not settings.demo_mode:
        raise http_error(
            status.HTTP_501_NOT_IMPLEMENTED,
            "auth_not_implemented",
            "Non-demo auth Coming Soon",
        )

    email = body.email.strip().lower()
    client_host = request.client.host if request.client else "unknown"
    rate_key = f"{client_host}:{email}"
    # Sync limiter max with settings (smallest safe hardening)
    login_rate_limiter.max_calls = max(1, settings.login_rate_limit_per_minute)
    if not login_rate_limiter.allow(rate_key):
        raise http_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            "Too many login attempts. Try again shortly.",
            {"retry_after_seconds": 60},
        )

    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.organization))
        .filter(User.email == email, User.is_active.is_(True))
        .one_or_none()
    )
    if user is None or not verify_password(body.password, user.password_hash):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_credentials",
            "Invalid email or password",
        )

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role_code=user.role.code,
        email=user.email,
        settings=settings,
    )
    return DemoLoginResponse(
        access_token=token,
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.code,
        display_name=user.display_name,
        email=user.email,
        message=(
            "Demo login — local JWT; not production auth. "
            f"Token TTL ~{settings.jwt_access_token_hours}h. "
            f"Production password policy target: min {settings.password_min_length} chars."
        ),
    )
