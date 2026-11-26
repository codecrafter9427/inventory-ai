"""Purchase order and receiving API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_sku: str | None = None
    product_name: str | None = None
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_cost: Decimal
    quantity_remaining: Decimal | None = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    supplier_id: UUID
    supplier_name: str | None = None
    location_id: UUID
    location_name: str | None = None
    po_number: str
    status: str
    ordered_at: datetime | None = None
    expected_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    status: str
    supplier_id: UUID
    supplier_name: str | None = None
    location_id: UUID
    location_name: str | None = None
    ordered_at: datetime | None = None
    expected_at: datetime | None = None
    line_count: int = 0


class ReceiveLineRequest(BaseModel):
    purchase_order_line_id: UUID
    quantity: Decimal = Field(..., gt=0, decimal_places=4)


class ReceiveRequest(BaseModel):
    purchase_order_id: UUID
    lines: list[ReceiveLineRequest] = Field(..., min_length=1)
    discrepancy_notes: str | None = None


class ReceiveLineResult(BaseModel):
    purchase_order_line_id: UUID
    product_id: UUID
    quantity_received_this_time: Decimal
    quantity_received_total: Decimal
    quantity_ordered: Decimal
    balance_after: Decimal
    movement_id: UUID


class ReceiveResponse(BaseModel):
    purchase_order_id: UUID
    po_number: str
    status: str
    location_id: UUID
    discrepancy_notes: str | None = None
    lines: list[ReceiveLineResult]
