"""Settings API schemas — org, roles, units, reorder defaults."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None = None


class UnitCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=80)


class UnitDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    name: str
    created_at: datetime
    updated_at: datetime


class OrganizationSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    default_reorder_point: Decimal
    default_safety_stock: Decimal
    default_lead_time_days: int


class OrganizationSettingsUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    default_reorder_point: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    default_safety_stock: Decimal | None = Field(default=None, ge=0, decimal_places=4)
    default_lead_time_days: int | None = Field(default=None, ge=0)
