"""Inventory reports and dashboard KPI schemas (deterministic)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class StockOnHandRow(BaseModel):
    product_id: UUID
    sku: str
    name: str
    location_id: UUID
    location_code: str
    location_name: str
    quantity: Decimal
    unit_cost: Decimal
    extended_value: Decimal
    reorder_point: Decimal
    is_low_stock: bool


class MovementReportRow(BaseModel):
    id: UUID
    created_at: datetime
    movement_type: str
    sku: str | None
    product_name: str | None
    location_code: str | None
    quantity: Decimal
    balance_after: Decimal
    reason: str | None = None


class InventoryReportSummary(BaseModel):
    generated_at: datetime
    stock_value: Decimal
    balance_rows: int
    low_stock_items: int
    out_of_stock_items: int
    pending_purchase_orders: int
    recent_movement_count: int
    stock_on_hand: list[StockOnHandRow] = Field(default_factory=list)
    recent_movements: list[MovementReportRow] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    generated_at: datetime
    stock_value: Decimal
    low_stock_items: int
    out_of_stock_items: int
    pending_purchase_orders: int
    recent_movement_count: int
    product_count: int
    location_count: int
