"""Stock balance and movement API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StockBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    product_id: UUID
    product_sku: str | None = None
    product_name: str | None = None
    location_id: UUID
    location_code: str | None = None
    location_name: str | None = None
    quantity: Decimal
    updated_at: datetime


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    product_id: UUID
    product_sku: str | None = None
    product_name: str | None = None
    location_id: UUID
    location_code: str | None = None
    location_name: str | None = None
    movement_type: str
    quantity: Decimal
    balance_after: Decimal
    reference_type: str | None = None
    reference_id: UUID | None = None
    reason: str | None = None
    actor_user_id: UUID | None = None
    created_at: datetime


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    address: str | None = None
    bin_shelf_notes: str | None = None
