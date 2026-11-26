"""Deterministic inventory reports and dashboard KPIs."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import Location, Product, PurchaseOrder, StockBalance, StockMovement
from app.schemas.reports import (
    DashboardSummary,
    InventoryReportSummary,
    MovementReportRow,
    StockOnHandRow,
)

PENDING_PO_STATUSES = frozenset({"draft", "ordered", "partially_received"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_stock_on_hand_rows(
    db: Session,
    organization_id: UUID,
    *,
    low_only: bool = False,
) -> list[StockOnHandRow]:
    rows = (
        db.query(StockBalance)
        .options(joinedload(StockBalance.product), joinedload(StockBalance.location))
        .filter(StockBalance.organization_id == organization_id)
        .order_by(StockBalance.updated_at.desc())
        .all()
    )
    out: list[StockOnHandRow] = []
    for bal in rows:
        product = bal.product
        location = bal.location
        if product is None or location is None:
            continue
        qty = Decimal(bal.quantity)
        cost = Decimal(product.cost)
        reorder = Decimal(product.reorder_point)
        is_low = qty <= reorder
        if low_only and not is_low:
            continue
        out.append(
            StockOnHandRow(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                location_id=location.id,
                location_code=location.code,
                location_name=location.name,
                quantity=qty,
                unit_cost=cost,
                extended_value=(qty * cost).quantize(Decimal("0.0001")),
                reorder_point=reorder,
                is_low_stock=is_low,
            )
        )
    return out


def build_movement_rows(
    db: Session,
    organization_id: UUID,
    *,
    limit: int = 200,
) -> list[MovementReportRow]:
    rows = (
        db.query(StockMovement)
        .options(joinedload(StockMovement.product), joinedload(StockMovement.location))
        .filter(StockMovement.organization_id == organization_id)
        .order_by(StockMovement.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        MovementReportRow(
            id=m.id,
            created_at=m.created_at,
            movement_type=m.movement_type,
            sku=m.product.sku if m.product else None,
            product_name=m.product.name if m.product else None,
            location_code=m.location.code if m.location else None,
            quantity=m.quantity,
            balance_after=m.balance_after,
            reason=m.reason,
        )
        for m in rows
    ]


def inventory_report(
    db: Session,
    organization_id: UUID,
    *,
    movement_limit: int = 50,
) -> InventoryReportSummary:
    soh = build_stock_on_hand_rows(db, organization_id)
    stock_value = sum((r.extended_value for r in soh), Decimal("0"))
    low = sum(1 for r in soh if r.is_low_stock and r.quantity > 0)
    out_of_stock = sum(1 for r in soh if r.quantity <= 0)
    pending_pos = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.organization_id == organization_id,
            PurchaseOrder.status.in_(PENDING_PO_STATUSES),
        )
        .count()
    )
    recent = build_movement_rows(db, organization_id, limit=movement_limit)
    return InventoryReportSummary(
        generated_at=_utc_now(),
        stock_value=stock_value,
        balance_rows=len(soh),
        low_stock_items=low,
        out_of_stock_items=out_of_stock,
        pending_purchase_orders=pending_pos,
        recent_movement_count=len(recent),
        stock_on_hand=soh,
        recent_movements=recent,
    )


def dashboard_summary(db: Session, organization_id: UUID) -> DashboardSummary:
    report = inventory_report(db, organization_id, movement_limit=30)
    product_count = (
        db.query(Product)
        .filter(
            Product.organization_id == organization_id,
            Product.archived_at.is_(None),
            Product.is_active.is_(True),
        )
        .count()
    )
    location_count = (
        db.query(Location)
        .filter(Location.organization_id == organization_id, Location.is_active.is_(True))
        .count()
    )
    return DashboardSummary(
        generated_at=report.generated_at,
        stock_value=report.stock_value,
        low_stock_items=report.low_stock_items,
        out_of_stock_items=report.out_of_stock_items,
        pending_purchase_orders=report.pending_purchase_orders,
        recent_movement_count=report.recent_movement_count,
        product_count=product_count,
        location_count=location_count,
    )


def stock_on_hand_csv(db: Session, organization_id: UUID) -> str:
    rows = build_stock_on_hand_rows(db, organization_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "sku",
            "name",
            "location_code",
            "location_name",
            "quantity",
            "unit_cost",
            "extended_value",
            "reorder_point",
            "is_low_stock",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.sku,
                r.name,
                r.location_code,
                r.location_name,
                str(r.quantity),
                str(r.unit_cost),
                str(r.extended_value),
                str(r.reorder_point),
                "true" if r.is_low_stock else "false",
            ]
        )
    return buf.getvalue()


def movements_csv(db: Session, organization_id: UUID, *, limit: int = 500) -> str:
    rows = build_movement_rows(db, organization_id, limit=limit)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "created_at",
            "movement_type",
            "sku",
            "product_name",
            "location_code",
            "quantity",
            "balance_after",
            "reason",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.created_at.isoformat(),
                r.movement_type,
                r.sku or "",
                r.product_name or "",
                r.location_code or "",
                str(r.quantity),
                str(r.balance_after),
                (r.reason or "").replace("\n", " "),
            ]
        )
    return buf.getvalue()
