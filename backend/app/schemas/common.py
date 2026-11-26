"""Shared API response shapes."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class ComingSoonResponse(BaseModel):
    status: str = "coming_soon"
    message: str = "This endpoint is not implemented yet."
    feature: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "inventory-ai"
    version: str = "0.4.0"


class DemoLoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@demo.inventory.local"])
    password: str = Field(..., examples=["demo-password"])


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    organization_id: UUID
    role: str
    display_name: str
    email: str
    demo: bool = True
    message: str = "Demo login — local JWT; not production auth."


class MeResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str
    role: str
    organization_id: UUID
    organization_name: str
    organization_slug: str


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str


class AIResultEnvelope(BaseModel):
    """Baseline AI response shape from portfolio requirements."""

    result: dict[str, Any]
    explanation: str
    sources: list[dict[str, str]] = Field(default_factory=list)
    requires_confirmation: bool = True
