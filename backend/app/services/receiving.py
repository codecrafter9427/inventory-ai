"""Atomic purchase-order receiving — balance + immutable ledger in one transaction."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.dependencies import AuthContext
from app.errors import http_error
from app.models import PurchaseOrder, PurchaseOrderLine, StockBalance, StockMovement
from app.schemas.purchase_order import ReceiveLineResult, ReceiveRequest, ReceiveResponse

RECEIVABLE_STATUSES = frozenset({"ordered", "partially_received"})


def receive_purchase_order(
    db: Session,
    auth: AuthContext,
    payload: ReceiveRequest,
) -> ReceiveResponse:
    """
    Receive quantities against a PO.

    Updates StockBalance and inserts immutable StockMovement rows atomically.
    Caller should commit the session after success.
    """
    po = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.lines))
        .filter(
            PurchaseOrder.id == payload.purchase_order_id,
            PurchaseOrder.organization_id == auth.organization_id,
        )
        .one_or_none()
    )
    if po is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Purchase order not found")

    if po.status not in RECEIVABLE_STATUSES:
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_po_status",
            f"Cannot receive against PO in status '{po.status}'",
            {"status": po.status, "allowed": sorted(RECEIVABLE_STATUSES)},
        )

    lines_by_id: dict[UUID, PurchaseOrderLine] = {line.id: line for line in po.lines}
    results: list[ReceiveLineResult] = []

    for item in payload.lines:
        line = lines_by_id.get(item.purchase_order_line_id)
        if line is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_line",
                "Purchase order line does not belong to this PO",
                {"purchase_order_line_id": str(item.purchase_order_line_id)},
            )

        qty = Decimal(item.quantity)
        remaining = line.quantity_ordered - line.quantity_received
        if qty > remaining:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "over_receive",
                "Receive quantity exceeds remaining ordered quantity",
                {
                    "purchase_order_line_id": str(line.id),
                    "quantity": str(qty),
                    "remaining": str(remaining),
                },
            )

        line.quantity_received = line.quantity_received + qty

        balance = db.execute(
            select(StockBalance)
            .where(
                StockBalance.organization_id == auth.organization_id,
                StockBalance.product_id == line.product_id,
                StockBalance.location_id == po.location_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if balance is None:
            balance = StockBalance(
                organization_id=auth.organization_id,
                product_id=line.product_id,
                location_id=po.location_id,
                quantity=Decimal("0"),
            )
            db.add(balance)
            db.flush()

        balance.quantity = balance.quantity + qty
        balance_after = balance.quantity

        reason_parts = [f"Received against {po.po_number}"]
        if payload.discrepancy_notes:
            reason_parts.append(payload.discrepancy_notes)
        movement = StockMovement(
            organization_id=auth.organization_id,
            product_id=line.product_id,
            location_id=po.location_id,
            movement_type="receive",
            quantity=qty,
            balance_after=balance_after,
            reference_type="purchase_order",
            reference_id=po.id,
            reason=" — ".join(reason_parts),
            actor_user_id=auth.user_id,
        )
        db.add(movement)
        db.flush()

        results.append(
            ReceiveLineResult(
                purchase_order_line_id=line.id,
                product_id=line.product_id,
                quantity_received_this_time=qty,
                quantity_received_total=line.quantity_received,
                quantity_ordered=line.quantity_ordered,
                balance_after=balance_after,
                movement_id=movement.id,
            )
        )

    # Refresh line quantities from in-memory state
    all_complete = all(ln.quantity_received >= ln.quantity_ordered for ln in po.lines)
    any_received = any(ln.quantity_received > 0 for ln in po.lines)
    if all_complete:
        po.status = "received"
    elif any_received:
        po.status = "partially_received"

    if payload.discrepancy_notes:
        note = payload.discrepancy_notes.strip()
        if note:
            existing = (po.notes or "").strip()
            po.notes = f"{existing}\nDiscrepancy: {note}".strip() if existing else f"Discrepancy: {note}"

    db.flush()

    return ReceiveResponse(
        purchase_order_id=po.id,
        po_number=po.po_number,
        status=po.status,
        location_id=po.location_id,
        discrepancy_notes=payload.discrepancy_notes,
        lines=results,
    )
