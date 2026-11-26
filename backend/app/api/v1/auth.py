"""Demo login placeholder — not production authentication."""

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_current_settings
from app.schemas.common import DemoLoginRequest, DemoLoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-login", response_model=DemoLoginResponse)
async def demo_login(
    body: DemoLoginRequest,
    settings: Settings = Depends(get_current_settings),
) -> DemoLoginResponse:
    """Accept demo credentials and return a placeholder bearer token."""
    email_ok = body.email.lower() == settings.demo_admin_email.lower()
    password_ok = body.password == settings.demo_admin_password
    if not (email_ok and password_ok):
        # Still allow any credentials in scaffold demo mode with a warning role
        return DemoLoginResponse(
            access_token="demo-token",
            role="staff",
            display_name=body.email.split("@")[0] or "Demo User",
            message="Demo login accepted (scaffold). Use documented demo credentials for Owner role.",
        )
    return DemoLoginResponse(
        access_token="demo-token",
        role="owner",
        display_name="Demo Owner",
        message="Demo login placeholder — not production auth.",
    )
