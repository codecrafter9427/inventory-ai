"""FastAPI dependencies (demo auth placeholder)."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.config import Settings, get_settings


def get_current_settings() -> Settings:
    return get_settings()


def get_provider() -> AIProvider:
    return get_ai_provider()


async def require_demo_token(
    authorization: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_current_settings),
) -> dict[str, str]:
    """Placeholder auth — accepts Bearer demo-token or any token when DEMO_MODE=true."""
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"error": {"code": "auth_not_implemented", "message": "Non-demo auth Coming Soon", "details": None}},
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "unauthorized", "message": "Missing Bearer token", "details": None}},
        )
    return {"sub": "demo-user", "role": "owner", "org_id": "demo-org"}
