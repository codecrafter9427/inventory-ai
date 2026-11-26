"""List pagination helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
