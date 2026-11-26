"""Stock transfer API schemas (thin Milestone 4 slice)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransferLineCreate(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., gt=0)

    @field_validator("quantity", mode="before")
    @classmethod
    def _qty(cls, v: object) -> object:
        return v


class TransferCreateRequest(BaseModel):
    source_location_id: UUID
    destination_location_id: UUID
    lines: list[TransferLineCreate] = Field(..., min_length=1)
    notes: str | None = None
    mark_in_transit: bool = True


class TransferLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_sku: str | None = None
    product_name: str | None = None
    quantity: Decimal


class TransferSummary(BaseModel):
    id: UUID
    status: str
    source_location_id: UUID
    source_location_code: str | None = None
    source_location_name: str | None = None
    destination_location_id: UUID
    destination_location_code: str | None = None
    destination_location_name: str | None = None
    line_count: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class TransferDetail(TransferSummary):
    lines: list[TransferLineResponse]


class TransferReceiveResponse(BaseModel):
    transfer_id: UUID
    status: str
    source_total_delta: Decimal
    destination_total_delta: Decimal
    preserved_total: bool
