"""Ledger integrity — StockBalance quantities vs sum of StockMovement quantities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import StockBalance, StockMovement


@dataclass(frozen=True)
class LedgerMismatch:
    organization_id: UUID
    product_id: UUID
    location_id: UUID
    balance_quantity: Decimal
    movements_sum: Decimal

    @property
    def delta(self) -> Decimal:
        return self.balance_quantity - self.movements_sum


@dataclass(frozen=True)
class LedgerIntegrityReport:
    organization_id: UUID
    balance_rows: int
    movement_groups: int
    mismatches: list[LedgerMismatch]

    @property
    def ok(self) -> bool:
        return len(self.mismatches) == 0


def verify_ledger_integrity(
    db: Session,
    organization_id: UUID,
    *,
    product_id: UUID | None = None,
    location_id: UUID | None = None,
) -> LedgerIntegrityReport:
    """
    Compare each StockBalance.quantity to SUM(StockMovement.quantity) for the
    same org/product/location. Opening + signed movements should equal balance.
    """
    bal_q = select(StockBalance).where(StockBalance.organization_id == organization_id)
    if product_id is not None:
        bal_q = bal_q.where(StockBalance.product_id == product_id)
    if location_id is not None:
        bal_q = bal_q.where(StockBalance.location_id == location_id)
    balances = list(db.scalars(bal_q).all())

    mov_q = (
        select(
            StockMovement.product_id,
            StockMovement.location_id,
            func.coalesce(func.sum(StockMovement.quantity), 0),
        )
        .where(StockMovement.organization_id == organization_id)
        .group_by(StockMovement.product_id, StockMovement.location_id)
    )
    if product_id is not None:
        mov_q = mov_q.where(StockMovement.product_id == product_id)
    if location_id is not None:
        mov_q = mov_q.where(StockMovement.location_id == location_id)

    sums: dict[tuple[UUID, UUID], Decimal] = {}
    for pid, lid, total in db.execute(mov_q).all():
        sums[(pid, lid)] = Decimal(total)

    mismatches: list[LedgerMismatch] = []
    for bal in balances:
        key = (bal.product_id, bal.location_id)
        mov_sum = sums.get(key, Decimal("0"))
        bal_qty = Decimal(bal.quantity)
        if bal_qty != mov_sum:
            mismatches.append(
                LedgerMismatch(
                    organization_id=organization_id,
                    product_id=bal.product_id,
                    location_id=bal.location_id,
                    balance_quantity=bal_qty,
                    movements_sum=mov_sum,
                )
            )

    # Movements without a balance row also count as mismatches (orphan ledger)
    balance_keys = {(b.product_id, b.location_id) for b in balances}
    for (pid, lid), mov_sum in sums.items():
        if (pid, lid) not in balance_keys and mov_sum != 0:
            mismatches.append(
                LedgerMismatch(
                    organization_id=organization_id,
                    product_id=pid,
                    location_id=lid,
                    balance_quantity=Decimal("0"),
                    movements_sum=mov_sum,
                )
            )

    return LedgerIntegrityReport(
        organization_id=organization_id,
        balance_rows=len(balances),
        movement_groups=len(sums),
        mismatches=mismatches,
    )
