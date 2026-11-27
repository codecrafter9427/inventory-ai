"""Supplier API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    lead_time_days: int = Field(default=7, ge=0)
    notes: str | None = None
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    lead_time_days: int | None = Field(default=None, ge=0)
    notes: str | None = None
    is_active: bool | None = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    lead_time_days: int
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
