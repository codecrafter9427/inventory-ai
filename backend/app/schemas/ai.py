"""Typed AI request/response schemas (validated I/O)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AISource(BaseModel):
    type: str
    id: str
    label: str


class AIResultEnvelope(BaseModel):
    result: dict[str, Any]
    explanation: str
    sources: list[AISource] = Field(default_factory=list)
    requires_confirmation: bool = True


class ReorderRecommendationsRequest(BaseModel):
    product_ids: list[UUID] = Field(default_factory=list)
    lookback_days: int = Field(default=30, ge=1, le=365)
    only_actionable: bool = True
    limit: int = Field(default=25, ge=1, le=100)


class ReorderLineResult(BaseModel):
    product_id: UUID
    sku: str
    name: str
    on_hand: Decimal
    avg_daily_movement: Decimal
    lead_time_days: int
    reorder_point: Decimal
    safety_stock: Decimal
    recommended_qty: Decimal
    below_reorder_point: bool
    assumptions: list[str]


class InventoryQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be empty")
        return cleaned


class StockoutRadarRequest(BaseModel):
    product_id: UUID | None = None
    lookback_days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=20, ge=1, le=100)
    # Optional manual overrides for formula demos / unit tests
    on_hand: Decimal | None = None
    avg_daily_movement: Decimal | None = None
    supplier_lead_time_days: Decimal | None = None
    safety_stock: Decimal | None = None


class ConfirmDraftPOLine(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., gt=0, decimal_places=4)


class ConfirmDraftPORequest(BaseModel):
    confirm: bool = False
    lines: list[ConfirmDraftPOLine] = Field(default_factory=list)
    supplier_id: UUID | None = None
    location_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=500)


class ConfirmDraftPOResult(BaseModel):
    purchase_order_id: UUID
    po_number: str
    status: str
    supplier_name: str | None
    location_name: str | None
    line_count: int
