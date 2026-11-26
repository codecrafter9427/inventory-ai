"""Purchase order receive — atomic balance + immutable movement tests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Location,
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
    StockBalance,
    StockMovement,
    Supplier,
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_receivable_po(db: Session, org: Organization) -> PurchaseOrder:
    supplier = db.query(Supplier).filter(Supplier.organization_id == org.id).first()
    location = db.query(Location).filter(Location.organization_id == org.id).first()
    product = (
        db.query(Product)
        .filter(Product.organization_id == org.id, Product.archived_at.is_(None))
        .order_by(Product.sku.asc())
        .first()
    )
    assert supplier and location and product
    po = PurchaseOrder(
        organization_id=org.id,
        supplier_id=supplier.id,
        location_id=location.id,
        po_number=f"PO-TEST-{datetime.now(timezone.utc).strftime('%H%M%S%f')}",
        status="ordered",
        ordered_at=datetime.now(timezone.utc),
        notes="API test receivable PO",
    )
    db.add(po)
    db.flush()
    line = PurchaseOrderLine(
        purchase_order_id=po.id,
        product_id=product.id,
        quantity_ordered=Decimal("10.0000"),
        quantity_received=Decimal("0"),
        unit_cost=product.cost,
    )
    db.add(line)
    db.commit()
    return (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.lines))
        .filter(PurchaseOrder.id == po.id)
        .one()
    )


def test_receive_updates_balance_and_movement_atomically(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    po = _make_receivable_po(db, primary_org)
    line = po.lines[0]
    qty = Decimal("2.0000")

    before_bal = db.execute(
        select(StockBalance).where(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == line.product_id,
            StockBalance.location_id == po.location_id,
        )
    ).scalar_one_or_none()
    before_qty = before_bal.quantity if before_bal else Decimal("0")
    before_moves = (
        db.query(StockMovement)
        .filter(
            StockMovement.organization_id == primary_org.id,
            StockMovement.reference_type == "purchase_order",
            StockMovement.reference_id == po.id,
        )
        .count()
    )

    res = client.post(
        "/api/v1/receipts",
        headers=_auth(admin_token),
        json={
            "purchase_order_id": str(po.id),
            "discrepancy_notes": "M2 demo receive",
            "lines": [
                {
                    "purchase_order_line_id": str(line.id),
                    "quantity": str(qty),
                }
            ],
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["purchase_order_id"] == str(po.id)
    assert body["status"] == "partially_received"
    assert len(body["lines"]) == 1
    assert Decimal(body["lines"][0]["quantity_received_this_time"]) == qty

    db.expire_all()
    after_bal = db.execute(
        select(StockBalance).where(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == line.product_id,
            StockBalance.location_id == po.location_id,
        )
    ).scalar_one()
    assert after_bal.quantity == before_qty + qty

    after_moves = (
        db.query(StockMovement)
        .filter(
            StockMovement.organization_id == primary_org.id,
            StockMovement.reference_type == "purchase_order",
            StockMovement.reference_id == po.id,
            StockMovement.movement_type == "receive",
        )
        .order_by(StockMovement.created_at.desc())
        .all()
    )
    assert len(after_moves) == before_moves + 1
    latest = after_moves[0]
    assert latest.quantity == qty
    assert latest.balance_after == after_bal.quantity
    assert "M2 demo receive" in (latest.reason or "")


def test_receive_rejects_over_quantity(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    po = _make_receivable_po(db, primary_org)
    line = po.lines[0]
    res = client.post(
        "/api/v1/receipts",
        headers=_auth(admin_token),
        json={
            "purchase_order_id": str(po.id),
            "lines": [
                {
                    "purchase_order_line_id": str(line.id),
                    "quantity": "99.0000",
                }
            ],
        },
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "over_receive"


def test_other_org_cannot_receive_primary_po(
    client: TestClient,
    other_org_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    po = _make_receivable_po(db, primary_org)
    line = po.lines[0]
    res = client.post(
        "/api/v1/receipts",
        headers=_auth(other_org_token),
        json={
            "purchase_order_id": str(po.id),
            "lines": [
                {
                    "purchase_order_line_id": str(line.id),
                    "quantity": "1.0000",
                }
            ],
        },
    )
    assert res.status_code == 404


def test_stock_balances_and_movements_readable(
    client: TestClient,
    admin_token: str,
) -> None:
    balances = client.get("/api/v1/stock/balances?page_size=10", headers=_auth(admin_token))
    assert balances.status_code == 200
    bal_body = balances.json()
    assert bal_body["total"] >= 1
    assert "quantity" in bal_body["items"][0]

    movements = client.get("/api/v1/stock/movements?page_size=10", headers=_auth(admin_token))
    assert movements.status_code == 200
    mov_body = movements.json()
    assert mov_body["total"] >= 1
    assert mov_body["items"][0]["movement_type"]


def test_list_purchase_orders(client: TestClient, admin_token: str) -> None:
    res = client.get("/api/v1/purchase-orders", headers=_auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 8
    detail_id = body["items"][0]["id"]
    detail = client.get(f"/api/v1/purchase-orders/{detail_id}", headers=_auth(admin_token))
    assert detail.status_code == 200
    assert "lines" in detail.json()
