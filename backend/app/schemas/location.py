"""Location write/read API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=160)
    address: str | None = None
    bin_shelf_notes: str | None = None
    is_active: bool = True


class LocationUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    address: str | None = None
    bin_shelf_notes: str | None = None
    is_active: bool | None = None


class LocationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    code: str
    name: str
    address: str | None = None
    bin_shelf_notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
