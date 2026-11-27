"""Purchase order read + create/edit/submit/cancel (receiving via /receipts)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import PurchaseOrder, PurchaseOrderLine
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.pagination import Page
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderLineResponse,
    PurchaseOrderResponse,
    PurchaseOrderSummary,
    PurchaseOrderUpdate,
)
from app.services import purchase_orders as po_service

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


def _line_response(line: PurchaseOrderLine) -> PurchaseOrderLineResponse:
    remaining = line.quantity_ordered - line.quantity_received
    return PurchaseOrderLineResponse(
        id=line.id,
        product_id=line.product_id,
        product_sku=line.product.sku if line.product else None,
        product_name=line.product.name if line.product else None,
        quantity_ordered=line.quantity_ordered,
        quantity_received=line.quantity_received,
        unit_cost=line.unit_cost,
        quantity_remaining=remaining if remaining > 0 else Decimal("0"),
    )


def _detail(po: PurchaseOrder) -> PurchaseOrderResponse:
    return PurchaseOrderResponse(
        id=po.id,
        organization_id=po.organization_id,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else None,
        location_id=po.location_id,
        location_name=po.location.name if po.location else None,
        po_number=po.po_number,
        status=po.status,
        ordered_at=po.ordered_at,
        expected_at=po.expected_at,
        notes=po.notes,
        created_at=po.created_at,
        updated_at=po.updated_at,
        lines=[_line_response(ln) for ln in po.lines],
    )


@router.get("", response_model=Page[PurchaseOrderSummary])
async def list_purchase_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[PurchaseOrderSummary]:
    query = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.location),
            selectinload(PurchaseOrder.lines),
        )
        .filter(PurchaseOrder.organization_id == auth.organization_id)
    )
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter)

    total = query.count()
    rows = (
        query.order_by(PurchaseOrder.po_number.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        PurchaseOrderSummary(
            id=po.id,
            po_number=po.po_number,
            status=po.status,
            supplier_id=po.supplier_id,
            supplier_name=po.supplier.name if po.supplier else None,
            location_id=po.location_id,
            location_name=po.location.name if po.location else None,
            ordered_at=po.ordered_at,
            expected_at=po.expected_at,
            line_count=len(po.lines) if po.lines else 0,
        )
        for po in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    body: PurchaseOrderCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    require_roles(auth, CATALOG_ROLES, action="create purchase orders")
    po = po_service.create_purchase_order(db, auth, body)
    db.commit()
    return _detail(po)


@router.get("/{purchase_order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    purchase_order_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.location),
            joinedload(PurchaseOrder.lines).joinedload(PurchaseOrderLine.product),
        )
        .filter(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.organization_id == auth.organization_id,
        )
        .one_or_none()
    )
    if po is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Purchase order not found")
    return _detail(po)


@router.patch("/{purchase_order_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    purchase_order_id: uuid.UUID,
    body: PurchaseOrderUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    require_roles(auth, CATALOG_ROLES, action="edit purchase orders")
    po = po_service.update_purchase_order(db, auth, purchase_order_id, body)
    db.commit()
    return _detail(po)


@router.post("/{purchase_order_id}/submit", response_model=PurchaseOrderResponse)
async def submit_purchase_order(
    purchase_order_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    require_roles(auth, CATALOG_ROLES, action="submit purchase orders")
    po = po_service.submit_purchase_order(db, auth, purchase_order_id)
    db.commit()
    return _detail(po)


@router.post("/{purchase_order_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_purchase_order(
    purchase_order_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PurchaseOrderResponse:
    require_roles(auth, CATALOG_ROLES, action="cancel purchase orders")
    po = po_service.cancel_purchase_order(db, auth, purchase_order_id)
    db.commit()
    return _detail(po)
