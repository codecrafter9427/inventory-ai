"""Stock count API schemas (thin approval slice)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CountLineCreate(BaseModel):
    product_id: UUID
    counted_quantity: Decimal = Field(..., ge=0)
    variance_reason: str | None = None


class CountCreateRequest(BaseModel):
    location_id: UUID
    lines: list[CountLineCreate] = Field(..., min_length=1)
    notes: str | None = None
    submit: bool = False


class CountLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_sku: str | None = None
    product_name: str | None = None
    expected_quantity: Decimal
    counted_quantity: Decimal
    variance: Decimal
    variance_reason: str | None = None


class CountSummary(BaseModel):
    id: UUID
    status: str
    location_id: UUID
    location_code: str | None = None
    location_name: str | None = None
    line_count: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None


class CountDetail(CountSummary):
    lines: list[CountLineResponse]


class CountApproveRequest(BaseModel):
    """Approve a submitted count. Variance lines require a reason."""

    approval_reason: str | None = None


class CountApproveResponse(BaseModel):
    count_id: UUID
    status: str
    adjustments_applied: int
