"""Thin stock-transfer workflow — preserve total quantity across locations."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.dependencies import AuthContext
from app.errors import http_error
from app.models import Location, Product, StockBalance, StockMovement, StockTransfer, StockTransferLine
from app.schemas.transfer import (
    TransferCreateRequest,
    TransferDetail,
    TransferLineResponse,
    TransferReceiveResponse,
    TransferSummary,
)


def _location_in_org(db: Session, org_id: UUID, location_id: UUID) -> Location:
    loc = (
        db.query(Location)
        .filter(Location.id == location_id, Location.organization_id == org_id)
        .one_or_none()
    )
    if loc is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Location not found")
    return loc


def _get_or_create_balance(
    db: Session,
    *,
    org_id: UUID,
    product_id: UUID,
    location_id: UUID,
) -> StockBalance:
    balance = db.execute(
        select(StockBalance)
        .where(
            StockBalance.organization_id == org_id,
            StockBalance.product_id == product_id,
            StockBalance.location_id == location_id,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if balance is None:
        balance = StockBalance(
            organization_id=org_id,
            product_id=product_id,
            location_id=location_id,
            quantity=Decimal("0"),
        )
        db.add(balance)
        db.flush()
    return balance


def _to_summary(t: StockTransfer, source: Location | None, dest: Location | None) -> TransferSummary:
    return TransferSummary(
        id=t.id,
        status=t.status,
        source_location_id=t.source_location_id,
        source_location_code=source.code if source else None,
        source_location_name=source.name if source else None,
        destination_location_id=t.destination_location_id,
        destination_location_code=dest.code if dest else None,
        destination_location_name=dest.name if dest else None,
        line_count=len(t.lines),
        notes=t.notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _to_detail(t: StockTransfer) -> TransferDetail:
    source = t.source_location if hasattr(t, "source_location") else None
    dest = t.destination_location if hasattr(t, "destination_location") else None
    # Locations may not be relationship-loaded under those names — fetch from lines' context
    summary = TransferSummary(
        id=t.id,
        status=t.status,
        source_location_id=t.source_location_id,
        source_location_code=None,
        source_location_name=None,
        destination_location_id=t.destination_location_id,
        destination_location_code=None,
        destination_location_name=None,
        line_count=len(t.lines),
        notes=t.notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )
    lines = [
        TransferLineResponse(
            id=ln.id,
            product_id=ln.product_id,
            product_sku=ln.product.sku if ln.product else None,
            product_name=ln.product.name if ln.product else None,
            quantity=ln.quantity,
        )
        for ln in t.lines
    ]
    return TransferDetail(**summary.model_dump(), lines=lines)


def serialize_transfer(db: Session, t: StockTransfer) -> TransferDetail:
    source = db.get(Location, t.source_location_id)
    dest = db.get(Location, t.destination_location_id)
    detail = _to_detail(t)
    detail.source_location_code = source.code if source else None
    detail.source_location_name = source.name if source else None
    detail.destination_location_code = dest.code if dest else None
    detail.destination_location_name = dest.name if dest else None
    return detail


def list_transfers(db: Session, org_id: UUID) -> list[TransferSummary]:
    rows = (
        db.query(StockTransfer)
        .options(joinedload(StockTransfer.lines))
        .filter(StockTransfer.organization_id == org_id)
        .order_by(StockTransfer.created_at.desc())
        .limit(100)
        .all()
    )
    out: list[TransferSummary] = []
    for t in rows:
        source = db.get(Location, t.source_location_id)
        dest = db.get(Location, t.destination_location_id)
        out.append(_to_summary(t, source, dest))
    return out


def get_transfer(db: Session, org_id: UUID, transfer_id: UUID) -> StockTransfer:
    t = (
        db.query(StockTransfer)
        .options(joinedload(StockTransfer.lines).joinedload(StockTransferLine.product))
        .filter(StockTransfer.id == transfer_id, StockTransfer.organization_id == org_id)
        .one_or_none()
    )
    if t is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Transfer not found")
    return t


def create_transfer(
    db: Session,
    auth: AuthContext,
    payload: TransferCreateRequest,
) -> StockTransfer:
    if payload.source_location_id == payload.destination_location_id:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_locations",
            "Source and destination locations must differ",
        )
    _location_in_org(db, auth.organization_id, payload.source_location_id)
    _location_in_org(db, auth.organization_id, payload.destination_location_id)

    for line in payload.lines:
        product = (
            db.query(Product)
            .filter(
                Product.id == line.product_id,
                Product.organization_id == auth.organization_id,
                Product.archived_at.is_(None),
            )
            .one_or_none()
        )
        if product is None:
            raise http_error(
                status.HTTP_404_NOT_FOUND,
                "not_found",
                "Product not found",
                {"product_id": str(line.product_id)},
            )

    transfer = StockTransfer(
        organization_id=auth.organization_id,
        source_location_id=payload.source_location_id,
        destination_location_id=payload.destination_location_id,
        status="in_transit" if payload.mark_in_transit else "initiated",
        notes=payload.notes,
        created_by_id=auth.user_id,
    )
    db.add(transfer)
    db.flush()
    for line in payload.lines:
        db.add(
            StockTransferLine(
                stock_transfer_id=transfer.id,
                product_id=line.product_id,
                quantity=Decimal(line.quantity),
            )
        )
    db.flush()
    return get_transfer(db, auth.organization_id, transfer.id)


def receive_transfer(
    db: Session,
    auth: AuthContext,
    transfer_id: UUID,
) -> TransferReceiveResponse:
    """
    Complete a transfer: transfer_out at source + transfer_in at destination.
    Total quantity across both locations is preserved for each product line.
    """
    transfer = get_transfer(db, auth.organization_id, transfer_id)
    if transfer.status not in {"initiated", "in_transit"}:
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_transfer_status",
            f"Cannot receive transfer in status '{transfer.status}'",
            {"status": transfer.status},
        )

    source_delta = Decimal("0")
    dest_delta = Decimal("0")

    for line in transfer.lines:
        qty = Decimal(line.quantity)
        source_bal = _get_or_create_balance(
            db,
            org_id=auth.organization_id,
            product_id=line.product_id,
            location_id=transfer.source_location_id,
        )
        if source_bal.quantity < qty:
            raise http_error(
                status.HTTP_409_CONFLICT,
                "insufficient_stock",
                "Source location does not have enough quantity for transfer",
                {
                    "product_id": str(line.product_id),
                    "available": str(source_bal.quantity),
                    "requested": str(qty),
                },
            )

        source_bal.quantity = source_bal.quantity - qty
        source_delta -= qty
        db.add(
            StockMovement(
                organization_id=auth.organization_id,
                product_id=line.product_id,
                location_id=transfer.source_location_id,
                movement_type="transfer_out",
                quantity=-qty,
                balance_after=source_bal.quantity,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                reason=f"Transfer out ({transfer.id})",
                actor_user_id=auth.user_id,
            )
        )

        dest_bal = _get_or_create_balance(
            db,
            org_id=auth.organization_id,
            product_id=line.product_id,
            location_id=transfer.destination_location_id,
        )
        dest_bal.quantity = dest_bal.quantity + qty
        dest_delta += qty
        db.add(
            StockMovement(
                organization_id=auth.organization_id,
                product_id=line.product_id,
                location_id=transfer.destination_location_id,
                movement_type="transfer_in",
                quantity=qty,
                balance_after=dest_bal.quantity,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                reason=f"Transfer in ({transfer.id})",
                actor_user_id=auth.user_id,
            )
        )

    transfer.status = "received"
    db.flush()

    return TransferReceiveResponse(
        transfer_id=transfer.id,
        status=transfer.status,
        source_total_delta=source_delta,
        destination_total_delta=dest_delta,
        preserved_total=(source_delta + dest_delta) == 0,
    )
