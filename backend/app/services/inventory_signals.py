"""Deterministic inventory signals used by reorder + Stockout Radar (org-scoped)."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Product, StockBalance, StockMovement, Supplier


OUTBOUND_TYPES = ("dispatch", "sale")
LOOKBACK_DAYS_DEFAULT = 30


@dataclass(frozen=True)
class ProductInventorySignal:
    product_id: uuid.UUID
    sku: str
    name: str
    on_hand: Decimal
    avg_daily_movement: Decimal
    reorder_point: Decimal
    safety_stock: Decimal
    lead_time_days: int
    movement_days_observed: int
    outbound_qty_abs: Decimal
    below_reorder_point: bool
    recommended_qty: Decimal
    assumptions: list[str]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sum_on_hand(db: Session, *, organization_id: uuid.UUID, product_id: uuid.UUID) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(StockBalance.quantity), 0))
        .filter(
            StockBalance.organization_id == organization_id,
            StockBalance.product_id == product_id,
        )
        .scalar()
    )
    return Decimal(total)


def avg_daily_outbound(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    lookback_days: int = LOOKBACK_DAYS_DEFAULT,
) -> tuple[Decimal, int, Decimal]:
    """Return (avg_daily, days_observed, total_outbound_abs) for dispatch/sale."""
    since = _utcnow() - timedelta(days=lookback_days)
    total = (
        db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(
            StockMovement.organization_id == organization_id,
            StockMovement.product_id == product_id,
            StockMovement.movement_type.in_(OUTBOUND_TYPES),
            StockMovement.created_at >= since,
        )
        .scalar()
    )
    # Outbound quantities are stored negative; use absolute for daily rate
    outbound_abs = abs(Decimal(total))
    days = max(lookback_days, 1)
    avg = (outbound_abs / Decimal(days)).quantize(Decimal("0.0001"))
    return avg, days, outbound_abs


def recommended_reorder_qty(
    *,
    on_hand: Decimal,
    avg_daily: Decimal,
    lead_time_days: int,
    safety_stock: Decimal,
    reorder_point: Decimal,
) -> tuple[Decimal, list[str]]:
    """
    Cover lead time + safety stock, respect reorder point.

    recommended = max(0, ceil(avg_daily * lead_time + safety_stock - on_hand),
                         ceil(reorder_point - on_hand) if below RP else 0)
    """
    assumptions = [
        f"Lookback outbound average used for daily movement ({avg_daily} units/day).",
        f"Lead time assumed at {lead_time_days} days from product catalog.",
        f"Safety stock from catalog: {safety_stock}.",
        f"Reorder point from catalog: {reorder_point}.",
        "Recommendation does not change stock; draft PO requires user confirmation.",
    ]
    cover_target = (avg_daily * Decimal(lead_time_days)) + safety_stock
    cover_gap = cover_target - on_hand
    rp_gap = reorder_point - on_hand if on_hand < reorder_point else Decimal("0")
    raw = max(cover_gap, rp_gap, Decimal("0"))
    qty = Decimal(0) if raw <= 0 else Decimal(math.ceil(float(raw)))
    if avg_daily <= 0:
        assumptions.append(
            "No outbound movement in lookback window; cover gap uses safety stock / reorder point only."
        )
    return qty, assumptions


def build_product_signal(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product: Product,
    lookback_days: int = LOOKBACK_DAYS_DEFAULT,
) -> ProductInventorySignal:
    on_hand = sum_on_hand(db, organization_id=organization_id, product_id=product.id)
    avg_daily, days, outbound_abs = avg_daily_outbound(
        db,
        organization_id=organization_id,
        product_id=product.id,
        lookback_days=lookback_days,
    )
    lead = int(product.lead_time_days or 7)
    qty, assumptions = recommended_reorder_qty(
        on_hand=on_hand,
        avg_daily=avg_daily,
        lead_time_days=lead,
        safety_stock=product.safety_stock or Decimal("0"),
        reorder_point=product.reorder_point or Decimal("0"),
    )
    return ProductInventorySignal(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        on_hand=on_hand,
        avg_daily_movement=avg_daily,
        reorder_point=product.reorder_point or Decimal("0"),
        safety_stock=product.safety_stock or Decimal("0"),
        lead_time_days=lead,
        movement_days_observed=days,
        outbound_qty_abs=outbound_abs,
        below_reorder_point=on_hand < (product.reorder_point or Decimal("0")),
        recommended_qty=qty,
        assumptions=assumptions,
    )


def list_product_signals(
    db: Session,
    *,
    organization_id: uuid.UUID,
    product_ids: list[uuid.UUID] | None = None,
    only_actionable: bool = True,
    lookback_days: int = LOOKBACK_DAYS_DEFAULT,
    limit: int = 50,
) -> list[ProductInventorySignal]:
    query = db.query(Product).filter(
        Product.organization_id == organization_id,
        Product.is_active.is_(True),
        Product.archived_at.is_(None),
    )
    if product_ids:
        query = query.filter(Product.id.in_(product_ids))
    products = query.order_by(Product.sku.asc()).limit(200).all()
    signals: list[ProductInventorySignal] = []
    for product in products:
        signal = build_product_signal(
            db,
            organization_id=organization_id,
            product=product,
            lookback_days=lookback_days,
        )
        if only_actionable and signal.recommended_qty <= 0 and not signal.below_reorder_point:
            continue
        signals.append(signal)
        if len(signals) >= limit:
            break
    # Prefer highest recommended qty / below RP first
    signals.sort(
        key=lambda s: (s.below_reorder_point, float(s.recommended_qty), -float(s.on_hand)),
        reverse=True,
    )
    return signals[:limit]


def default_supplier_for_org(db: Session, *, organization_id: uuid.UUID) -> Supplier | None:
    return (
        db.query(Supplier)
        .filter(Supplier.organization_id == organization_id, Supplier.is_active.is_(True))
        .order_by(Supplier.name.asc())
        .first()
    )
