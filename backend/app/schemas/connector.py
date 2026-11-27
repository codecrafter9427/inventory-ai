"""Insights connector (read-only) response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ConnectorHealthResponse(BaseModel):
    status: str = "ok"
    connector: str = "insights"
    version: str = "v1"
    service: str = "inventory-ai"


class InsightsSummaryResponse(BaseModel):
    generated_at: datetime
    organization_id: str
    inventory_value: Decimal
    low_stock_items: int
    out_of_stock_items: int
    pending_purchase_orders: int
    recent_movement_count: int
    product_count: int
    location_count: int
    balance_rows: int = Field(description="Stock balance row count")
