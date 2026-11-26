"""Create draft purchase orders only after explicit user confirmation (AI path)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models import AuditEvent, Location, Product, PurchaseOrder, PurchaseOrderLine, Supplier
from app.services.inventory_signals import default_supplier_for_org


def _next_po_number(db: Session, *, organization_id: uuid.UUID) -> str:
    existing = (
        db.query(PurchaseOrder.po_number)
        .filter(PurchaseOrder.organization_id == organization_id)
        .order_by(PurchaseOrder.po_number.desc())
        .limit(50)
        .all()
    )
    max_n = 0
    for (num,) in existing:
        # Prefer PO-YYYY-NNN pattern
        parts = num.rsplit("-", 1)
        if len(parts) == 2 and parts[-1].isdigit():
            max_n = max(max_n, int(parts[-1]))
    return f"PO-2026-{max_n + 1:03d}"


def create_draft_po_from_recommendations(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    lines: list[dict],
    supplier_id: uuid.UUID | None = None,
    location_id: uuid.UUID | None = None,
    notes: str | None = None,
) -> PurchaseOrder:
    """
    Persist a draft PO from confirmed AI reorder lines.

    Does not touch StockBalance / StockMovement.
    """
    if not lines:
        raise ValueError("At least one confirmed line is required")

    supplier: Supplier | None
    if supplier_id is not None:
        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id, Supplier.organization_id == organization_id)
            .one_or_none()
        )
    else:
        supplier = default_supplier_for_org(db, organization_id=organization_id)
    if supplier is None:
        raise ValueError("No supplier available for draft PO")

    if location_id is not None:
        location = (
            db.query(Location)
            .filter(Location.id == location_id, Location.organization_id == organization_id)
            .one_or_none()
        )
    else:
        location = (
            db.query(Location)
            .filter(Location.organization_id == organization_id, Location.is_active.is_(True))
            .order_by(Location.code.asc())
            .first()
        )
    if location is None:
        raise ValueError("No location available for draft PO")

    po = PurchaseOrder(
        organization_id=organization_id,
        supplier_id=supplier.id,
        location_id=location.id,
        po_number=_next_po_number(db, organization_id=organization_id),
        status="draft",
        notes=notes or "Draft created from AI reorder recommendations (user confirmed).",
        created_by_id=actor_user_id,
    )
    db.add(po)
    db.flush()

    for raw in lines:
        product_id = uuid.UUID(str(raw["product_id"]))
        qty = Decimal(str(raw["quantity"]))
        if qty <= 0:
            continue
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.organization_id == organization_id)
            .one_or_none()
        )
        if product is None:
            raise ValueError(f"Product not found in organization: {product_id}")
        db.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=product.id,
                quantity_ordered=qty,
                quantity_received=Decimal("0"),
                unit_cost=product.cost,
            )
        )

    db.add(
        AuditEvent(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="ai.confirm_draft_po",
            entity_type="purchase_order",
            entity_id=po.id,
            message=f"User confirmed AI draft PO {po.po_number}",
            details={"po_number": po.po_number, "line_count": len(lines)},
        )
    )
    db.commit()
    db.refresh(po)
    return (
        db.query(PurchaseOrder)
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.location),
            joinedload(PurchaseOrder.lines).joinedload(PurchaseOrderLine.product),
        )
        .filter(PurchaseOrder.id == po.id)
        .one()
    )
