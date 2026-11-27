"""Purchase order create / edit / submit / cancel (stock unchanged until receive)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import status
from sqlalchemy.orm import Session, joinedload

from app.dependencies import AuthContext
from app.errors import http_error
from app.models import Location, Product, PurchaseOrder, PurchaseOrderLine, Supplier
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate
from app.services.audit import record_audit
from app.services.draft_po import _next_po_number

EDITABLE_STATUSES = frozenset({"draft"})
SUBMITTABLE_STATUSES = frozenset({"draft"})
CANCELLABLE_STATUSES = frozenset({"draft", "ordered"})


def _load_po(db: Session, auth: AuthContext, po_id: uuid.UUID) -> PurchaseOrder:
    po = (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.location),
            joinedload(PurchaseOrder.lines).joinedload(PurchaseOrderLine.product),
        )
        .filter(
            PurchaseOrder.id == po_id,
            PurchaseOrder.organization_id == auth.organization_id,
        )
        .one_or_none()
    )
    if po is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Purchase order not found")
    return po


def _require_supplier(db: Session, org_id: uuid.UUID, supplier_id: uuid.UUID) -> Supplier:
    row = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.organization_id == org_id,
            Supplier.is_active.is_(True),
        )
        .one_or_none()
    )
    if row is None:
        raise http_error(status.HTTP_400_BAD_REQUEST, "invalid_supplier", "Supplier not found")
    return row


def _require_location(db: Session, org_id: uuid.UUID, location_id: uuid.UUID) -> Location:
    row = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.organization_id == org_id,
            Location.is_active.is_(True),
        )
        .one_or_none()
    )
    if row is None:
        raise http_error(status.HTTP_400_BAD_REQUEST, "invalid_location", "Location not found")
    return row


def _replace_lines(
    db: Session,
    po: PurchaseOrder,
    org_id: uuid.UUID,
    lines: list,
) -> None:
    po.lines.clear()
    db.flush()
    for raw in lines:
        product = (
            db.query(Product)
            .filter(
                Product.id == raw.product_id,
                Product.organization_id == org_id,
                Product.archived_at.is_(None),
            )
            .one_or_none()
        )
        if product is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_product",
                "Product not found in organization",
                {"product_id": str(raw.product_id)},
            )
        unit_cost = raw.unit_cost if raw.unit_cost is not None else product.cost
        db.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=product.id,
                quantity_ordered=Decimal(raw.quantity_ordered),
                quantity_received=Decimal("0"),
                unit_cost=Decimal(unit_cost),
            )
        )


def create_purchase_order(
    db: Session,
    auth: AuthContext,
    body: PurchaseOrderCreate,
) -> PurchaseOrder:
    _require_supplier(db, auth.organization_id, body.supplier_id)
    _require_location(db, auth.organization_id, body.location_id)

    po = PurchaseOrder(
        organization_id=auth.organization_id,
        supplier_id=body.supplier_id,
        location_id=body.location_id,
        po_number=_next_po_number(db, organization_id=auth.organization_id),
        status="draft",
        expected_at=body.expected_at,
        notes=body.notes,
        created_by_id=auth.user_id,
    )
    db.add(po)
    db.flush()
    _replace_lines(db, po, auth.organization_id, body.lines)

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="purchase_order.create",
        entity_type="purchase_order",
        entity_id=po.id,
        message=f"Created draft PO {po.po_number}",
        details={"po_number": po.po_number, "line_count": len(body.lines)},
    )
    db.flush()
    return _load_po(db, auth, po.id)


def update_purchase_order(
    db: Session,
    auth: AuthContext,
    po_id: uuid.UUID,
    body: PurchaseOrderUpdate,
) -> PurchaseOrder:
    po = _load_po(db, auth, po_id)
    if po.status not in EDITABLE_STATUSES:
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_po_status",
            f"Cannot edit PO in status '{po.status}'",
            {"status": po.status, "allowed": sorted(EDITABLE_STATUSES)},
        )

    data = body.model_dump(exclude_unset=True)
    if "supplier_id" in data and data["supplier_id"] is not None:
        _require_supplier(db, auth.organization_id, data["supplier_id"])
        po.supplier_id = data["supplier_id"]
    if "location_id" in data and data["location_id"] is not None:
        _require_location(db, auth.organization_id, data["location_id"])
        po.location_id = data["location_id"]
    if "notes" in data:
        po.notes = data["notes"]
    if "expected_at" in data:
        po.expected_at = data["expected_at"]
    if body.lines is not None:
        if len(body.lines) < 1:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_lines",
                "At least one line is required",
            )
        _replace_lines(db, po, auth.organization_id, body.lines)

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="purchase_order.update",
        entity_type="purchase_order",
        entity_id=po.id,
        message=f"Updated draft PO {po.po_number}",
        details={"po_number": po.po_number},
    )
    db.flush()
    return _load_po(db, auth, po.id)


def submit_purchase_order(db: Session, auth: AuthContext, po_id: uuid.UUID) -> PurchaseOrder:
    po = _load_po(db, auth, po_id)
    if po.status not in SUBMITTABLE_STATUSES:
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_po_status",
            f"Cannot submit PO in status '{po.status}'",
            {"status": po.status, "allowed": sorted(SUBMITTABLE_STATUSES)},
        )
    if not po.lines:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "empty_po",
            "Cannot submit a purchase order with no lines",
        )

    po.status = "ordered"
    po.ordered_at = datetime.now(timezone.utc)
    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="purchase_order.submit",
        entity_type="purchase_order",
        entity_id=po.id,
        message=f"Submitted PO {po.po_number}",
        details={"po_number": po.po_number, "status": po.status},
    )
    db.flush()
    return _load_po(db, auth, po.id)


def cancel_purchase_order(db: Session, auth: AuthContext, po_id: uuid.UUID) -> PurchaseOrder:
    po = _load_po(db, auth, po_id)
    if po.status not in CANCELLABLE_STATUSES:
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_po_status",
            f"Cannot cancel PO in status '{po.status}'",
            {"status": po.status, "allowed": sorted(CANCELLABLE_STATUSES)},
        )
    if any(ln.quantity_received > 0 for ln in po.lines):
        raise http_error(
            status.HTTP_409_CONFLICT,
            "already_received",
            "Cannot cancel a PO that has received quantity",
        )

    po.status = "cancelled"
    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="purchase_order.cancel",
        entity_type="purchase_order",
        entity_id=po.id,
        message=f"Cancelled PO {po.po_number}",
        details={"po_number": po.po_number},
    )
    db.flush()
    return _load_po(db, auth, po.id)
