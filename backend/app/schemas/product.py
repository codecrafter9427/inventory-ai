"""Product / category / unit API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    barcode: str | None = Field(default=None, max_length=64)
    category_id: UUID | None = None
    unit_id: UUID
    cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    selling_price: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    reorder_point: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    safety_stock: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    lead_time_days: int = Field(default=7, ge=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    barcode: str | None = Field(default=None, max_length=64)
    category_id: UUID | None = None
    unit_id: UUID | None = None
    cost: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    selling_price: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    reorder_point: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    safety_stock: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    lead_time_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    sku: str
    name: str
    description: str | None = None
    barcode: str | None = None
    category_id: UUID | None = None
    unit_id: UUID
    cost: Decimal
    selling_price: Decimal
    reorder_point: Decimal
    safety_stock: Decimal
    lead_time_days: int
    is_active: bool
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    unit_code: str | None = None
