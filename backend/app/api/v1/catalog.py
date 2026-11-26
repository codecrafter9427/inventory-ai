"""Read helpers for categories and units (product form support)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.models import Category, Unit
from app.schemas.product import CategoryResponse, UnitResponse

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[CategoryResponse]:
    rows = (
        db.query(Category)
        .filter(
            Category.organization_id == auth.organization_id,
            Category.archived_at.is_(None),
        )
        .order_by(Category.name.asc())
        .all()
    )
    return [CategoryResponse.model_validate(r) for r in rows]


@router.get("/units", response_model=list[UnitResponse])
async def list_units(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[UnitResponse]:
    rows = (
        db.query(Unit)
        .filter(Unit.organization_id == auth.organization_id)
        .order_by(Unit.code.asc())
        .all()
    )
    return [UnitResponse.model_validate(r) for r in rows]
