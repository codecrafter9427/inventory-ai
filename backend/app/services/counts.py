"""Thin stock-count workflow — variance requires approval reason."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.dependencies import AuthContext
from app.errors import http_error
from app.models import Location, Product, StockBalance, StockCount, StockCountLine, StockMovement
from app.schemas.count import (
    CountApproveRequest,
    CountApproveResponse,
    CountCreateRequest,
    CountDetail,
    CountLineResponse,
    CountSummary,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _balance_qty(db: Session, org_id: UUID, product_id: UUID, location_id: UUID) -> Decimal:
    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.organization_id == org_id,
            StockBalance.product_id == product_id,
            StockBalance.location_id == location_id,
        )
        .one_or_none()
    )
    return Decimal(bal.quantity) if bal else Decimal("0")


def _to_summary(c: StockCount, location: Location | None) -> CountSummary:
    return CountSummary(
        id=c.id,
        status=c.status,
        location_id=c.location_id,
        location_code=location.code if location else None,
        location_name=location.name if location else None,
        line_count=len(c.lines),
        notes=c.notes,
        created_at=c.created_at,
        updated_at=c.updated_at,
        approved_at=c.approved_at,
    )


def serialize_count(db: Session, c: StockCount) -> CountDetail:
    location = db.get(Location, c.location_id)
    summary = _to_summary(c, location)
    lines = [
        CountLineResponse(
            id=ln.id,
            product_id=ln.product_id,
            product_sku=ln.product.sku if ln.product else None,
            product_name=ln.product.name if ln.product else None,
            expected_quantity=ln.expected_quantity,
            counted_quantity=ln.counted_quantity,
            variance=Decimal(ln.counted_quantity) - Decimal(ln.expected_quantity),
            variance_reason=ln.variance_reason,
        )
        for ln in c.lines
    ]
    return CountDetail(**summary.model_dump(), lines=lines)


def list_counts(db: Session, org_id: UUID) -> list[CountSummary]:
    rows = (
        db.query(StockCount)
        .options(joinedload(StockCount.lines))
        .filter(StockCount.organization_id == org_id)
        .order_by(StockCount.created_at.desc())
        .limit(100)
        .all()
    )
    out: list[CountSummary] = []
    for c in rows:
        loc = db.get(Location, c.location_id)
        out.append(_to_summary(c, loc))
    return out


def get_count(db: Session, org_id: UUID, count_id: UUID) -> StockCount:
    c = (
        db.query(StockCount)
        .options(joinedload(StockCount.lines).joinedload(StockCountLine.product))
        .filter(StockCount.id == count_id, StockCount.organization_id == org_id)
        .one_or_none()
    )
    if c is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Stock count not found")
    return c


def create_count(db: Session, auth: AuthContext, payload: CountCreateRequest) -> StockCount:
    loc = (
        db.query(Location)
        .filter(Location.id == payload.location_id, Location.organization_id == auth.organization_id)
        .one_or_none()
    )
    if loc is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Location not found")

    count = StockCount(
        organization_id=auth.organization_id,
        location_id=payload.location_id,
        status="submitted" if payload.submit else "draft",
        notes=payload.notes,
        created_by_id=auth.user_id,
    )
    db.add(count)
    db.flush()

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
        expected = _balance_qty(db, auth.organization_id, line.product_id, payload.location_id)
        db.add(
            StockCountLine(
                stock_count_id=count.id,
                product_id=line.product_id,
                expected_quantity=expected,
                counted_quantity=Decimal(line.counted_quantity),
                variance_reason=line.variance_reason,
            )
        )
    db.flush()
    return get_count(db, auth.organization_id, count.id)


def submit_count(db: Session, auth: AuthContext, count_id: UUID) -> StockCount:
    count = get_count(db, auth.organization_id, count_id)
    if count.status != "draft":
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_count_status",
            f"Only draft counts can be submitted (status={count.status})",
        )
    count.status = "submitted"
    db.flush()
    return count


def approve_count(
    db: Session,
    auth: AuthContext,
    count_id: UUID,
    payload: CountApproveRequest,
) -> CountApproveResponse:
    """
    Approve a submitted count. Any non-zero variance requires a reason
    (line variance_reason or approval_reason). Applies adjustment movements.
    """
    count = get_count(db, auth.organization_id, count_id)
    if count.status != "submitted":
        raise http_error(
            status.HTTP_409_CONFLICT,
            "invalid_count_status",
            f"Only submitted counts can be approved (status={count.status})",
        )

    approval_reason = (payload.approval_reason or "").strip()
    for line in count.lines:
        variance = Decimal(line.counted_quantity) - Decimal(line.expected_quantity)
        if variance != 0:
            line_reason = (line.variance_reason or "").strip()
            if not line_reason and not approval_reason:
                raise http_error(
                    status.HTTP_400_BAD_REQUEST,
                    "variance_reason_required",
                    "Non-zero variance requires a reason before approval",
                    {
                        "product_id": str(line.product_id),
                        "variance": str(variance),
                    },
                )
            if not line_reason and approval_reason:
                line.variance_reason = approval_reason

    adjustments = 0
    for line in count.lines:
        variance = Decimal(line.counted_quantity) - Decimal(line.expected_quantity)
        if variance == 0:
            continue

        bal = db.execute(
            select(StockBalance)
            .where(
                StockBalance.organization_id == auth.organization_id,
                StockBalance.product_id == line.product_id,
                StockBalance.location_id == count.location_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if bal is None:
            bal = StockBalance(
                organization_id=auth.organization_id,
                product_id=line.product_id,
                location_id=count.location_id,
                quantity=Decimal("0"),
            )
            db.add(bal)
            db.flush()

        bal.quantity = Decimal(line.counted_quantity)
        reason = line.variance_reason or approval_reason or "Count variance approved"
        db.add(
            StockMovement(
                organization_id=auth.organization_id,
                product_id=line.product_id,
                location_id=count.location_id,
                movement_type="adjustment",
                quantity=variance,
                balance_after=bal.quantity,
                reference_type="stock_count",
                reference_id=count.id,
                reason=reason,
                actor_user_id=auth.user_id,
            )
        )
        adjustments += 1

    count.status = "approved"
    count.approved_by_id = auth.user_id
    count.approved_at = _utc_now()
    db.flush()

    return CountApproveResponse(
        count_id=count.id,
        status=count.status,
        adjustments_applied=adjustments,
    )
