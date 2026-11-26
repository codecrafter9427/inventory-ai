"""Stock balances and recent movements (read)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.models import Product, StockBalance, StockMovement
from app.schemas.pagination import Page
from app.schemas.stock import StockBalanceResponse, StockMovementResponse

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/balances", response_model=Page[StockBalanceResponse])
async def list_balances(
    q: str | None = Query(default=None, description="Filter by product SKU or name"),
    location_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[StockBalanceResponse]:
    query = (
        db.query(StockBalance)
        .options(joinedload(StockBalance.product), joinedload(StockBalance.location))
        .join(Product, StockBalance.product_id == Product.id)
        .filter(StockBalance.organization_id == auth.organization_id)
    )
    if location_id is not None:
        query = query.filter(StockBalance.location_id == location_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(Product.sku.ilike(term), Product.name.ilike(term)))

    total = query.count()
    rows = (
        query.order_by(StockBalance.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        StockBalanceResponse(
            id=b.id,
            organization_id=b.organization_id,
            product_id=b.product_id,
            product_sku=b.product.sku if b.product else None,
            product_name=b.product.name if b.product else None,
            location_id=b.location_id,
            location_code=b.location.code if b.location else None,
            location_name=b.location.name if b.location else None,
            quantity=b.quantity,
            updated_at=b.updated_at,
        )
        for b in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/movements", response_model=Page[StockMovementResponse])
async def list_movements(
    product_id: uuid.UUID | None = None,
    location_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[StockMovementResponse]:
    query = (
        db.query(StockMovement)
        .options(joinedload(StockMovement.product), joinedload(StockMovement.location))
        .filter(StockMovement.organization_id == auth.organization_id)
    )
    if product_id is not None:
        query = query.filter(StockMovement.product_id == product_id)
    if location_id is not None:
        query = query.filter(StockMovement.location_id == location_id)

    total = query.count()
    rows = (
        query.order_by(StockMovement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        StockMovementResponse(
            id=m.id,
            organization_id=m.organization_id,
            product_id=m.product_id,
            product_sku=m.product.sku if m.product else None,
            product_name=m.product.name if m.product else None,
            location_id=m.location_id,
            location_code=m.location.code if m.location else None,
            location_name=m.location.name if m.location else None,
            movement_type=m.movement_type,
            quantity=m.quantity,
            balance_after=m.balance_after,
            reference_type=m.reference_type,
            reference_id=m.reference_id,
            reason=m.reason,
            actor_user_id=m.actor_user_id,
            created_at=m.created_at,
        )
        for m in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)
