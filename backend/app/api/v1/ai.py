"""AI endpoint stubs — DemoAIProvider / optional Ollama stub (auth required)."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.provider import AIProvider
from app.dependencies import AuthContext, get_auth_context, get_provider
from app.schemas.common import AIResultEnvelope

router = APIRouter(prefix="/ai", tags=["ai"])


class AIRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    context_ids: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


@router.post("/reorder-recommendations", response_model=AIResultEnvelope)
async def reorder_recommendations(
    body: AIRequest,
    _auth: AuthContext = Depends(get_auth_context),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    return await provider.reorder_recommendations(
        input_payload=body.input,
        context_ids=body.context_ids,
        options=body.options,
    )


@router.post("/inventory-question", response_model=AIResultEnvelope)
async def inventory_question(
    body: AIRequest,
    _auth: AuthContext = Depends(get_auth_context),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    return await provider.inventory_question(
        input_payload=body.input,
        context_ids=body.context_ids,
        options=body.options,
    )


@router.post("/stockout-radar", response_model=AIResultEnvelope)
async def stockout_radar(
    body: AIRequest,
    _auth: AuthContext = Depends(get_auth_context),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    """Differentiator stub — transparent risk score via demo formula."""
    return await provider.stockout_radar(
        input_payload=body.input,
        context_ids=body.context_ids,
        options=body.options,
    )
