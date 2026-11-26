"""Milestone 4 — reports/CSV, transfer quantity preservation, count approval."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Location, Organization, Product, StockBalance


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_and_inventory_report(
    client: TestClient,
    admin_token: str,
) -> None:
    dash = client.get("/api/v1/dashboard/summary", headers=_auth(admin_token))
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert "stock_value" in body
    assert body["product_count"] >= 30
    assert body["pending_purchase_orders"] >= 0

    report = client.get("/api/v1/reports/inventory", headers=_auth(admin_token))
    assert report.status_code == 200, report.text
    data = report.json()
    assert data["balance_rows"] >= 1
    assert isinstance(data["stock_on_hand"], list)
    assert isinstance(data["recent_movements"], list)


def test_csv_exports_deterministic(
    client: TestClient,
    admin_token: str,
) -> None:
    soh = client.get("/api/v1/reports/inventory/stock-on-hand.csv", headers=_auth(admin_token))
    assert soh.status_code == 200, soh.text
    assert "text/csv" in soh.headers.get("content-type", "")
    text = soh.text
    assert "sku,name,location_code" in text.splitlines()[0]
    assert len(text.splitlines()) > 1

    mov = client.get("/api/v1/reports/inventory/movements.csv", headers=_auth(admin_token))
    assert mov.status_code == 200, mov.text
    assert "movement_type" in mov.text.splitlines()[0]

    # Same request again yields identical header + deterministic column order
    soh2 = client.get("/api/v1/reports/inventory/stock-on-hand.csv", headers=_auth(admin_token))
    assert soh2.text.splitlines()[0] == text.splitlines()[0]


def test_reports_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/reports/inventory").status_code == 401
    assert client.get("/api/v1/dashboard/summary").status_code == 401


def test_transfer_preserves_total_quantity(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    locations = (
        db.query(Location)
        .filter(Location.organization_id == primary_org.id, Location.is_active.is_(True))
        .order_by(Location.code.asc())
        .limit(2)
        .all()
    )
    assert len(locations) >= 2
    source, dest = locations[0], locations[1]

    product = (
        db.query(Product)
        .filter(Product.organization_id == primary_org.id, Product.archived_at.is_(None))
        .order_by(Product.sku.asc())
        .first()
    )
    assert product is not None

    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == source.id,
        )
        .one_or_none()
    )
    if bal is None:
        bal = StockBalance(
            organization_id=primary_org.id,
            product_id=product.id,
            location_id=source.id,
            quantity=Decimal("25.0000"),
        )
        db.add(bal)
        db.commit()
    elif bal.quantity < Decimal("5"):
        bal.quantity = Decimal("25.0000")
        db.commit()

    db.refresh(bal)
    qty = Decimal("3.0000")
    before_source = Decimal(bal.quantity)
    dest_before_row = (
        db.query(StockBalance)
        .filter(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == dest.id,
        )
        .one_or_none()
    )
    before_dest = Decimal(dest_before_row.quantity) if dest_before_row else Decimal("0")
    before_total = before_source + before_dest

    create = client.post(
        "/api/v1/stock/transfers",
        headers=_auth(admin_token),
        json={
            "source_location_id": str(source.id),
            "destination_location_id": str(dest.id),
            "lines": [{"product_id": str(product.id), "quantity": str(qty)}],
            "notes": "M4 test transfer",
            "mark_in_transit": True,
        },
    )
    assert create.status_code == 201, create.text
    transfer_id = create.json()["id"]
    assert create.json()["status"] == "in_transit"

    receive = client.post(
        f"/api/v1/stock/transfers/{transfer_id}/receive",
        headers=_auth(admin_token),
    )
    assert receive.status_code == 200, receive.text
    body = receive.json()
    assert body["status"] == "received"
    assert body["preserved_total"] is True
    assert Decimal(body["source_total_delta"]) + Decimal(body["destination_total_delta"]) == 0

    db.expire_all()
    after_source = db.execute(
        select(StockBalance).where(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == source.id,
        )
    ).scalar_one()
    after_dest = db.execute(
        select(StockBalance).where(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == dest.id,
        )
    ).scalar_one()
    assert Decimal(after_source.quantity) == before_source - qty
    assert Decimal(after_dest.quantity) == before_dest + qty
    assert Decimal(after_source.quantity) + Decimal(after_dest.quantity) == before_total


def test_count_variance_requires_reason_then_approves(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    location = (
        db.query(Location)
        .filter(Location.organization_id == primary_org.id)
        .order_by(Location.code.asc())
        .first()
    )
    product = (
        db.query(Product)
        .filter(Product.organization_id == primary_org.id, Product.archived_at.is_(None))
        .order_by(Product.sku.asc())
        .first()
    )
    assert location and product

    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == location.id,
        )
        .one_or_none()
    )
    if bal is None:
        bal = StockBalance(
            organization_id=primary_org.id,
            product_id=product.id,
            location_id=location.id,
            quantity=Decimal("10.0000"),
        )
        db.add(bal)
        db.commit()
    db.refresh(bal)
    expected = Decimal(bal.quantity)
    counted = expected + Decimal("2.0000")

    create = client.post(
        "/api/v1/stock/counts",
        headers=_auth(admin_token),
        json={
            "location_id": str(location.id),
            "submit": True,
            "lines": [
                {
                    "product_id": str(product.id),
                    "counted_quantity": str(counted),
                }
            ],
            "notes": "M4 count test",
        },
    )
    assert create.status_code == 201, create.text
    count_id = create.json()["id"]
    assert create.json()["status"] == "submitted"

    # Missing variance reason → 400
    bad = client.post(
        f"/api/v1/stock/counts/{count_id}/approve",
        headers=_auth(admin_token),
        json={},
    )
    assert bad.status_code == 400, bad.text
    assert bad.json()["error"]["code"] == "variance_reason_required"

    ok = client.post(
        f"/api/v1/stock/counts/{count_id}/approve",
        headers=_auth(admin_token),
        json={"approval_reason": "Cycle count variance confirmed"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "approved"
    assert ok.json()["adjustments_applied"] == 1

    db.expire_all()
    after = db.execute(
        select(StockBalance).where(
            StockBalance.organization_id == primary_org.id,
            StockBalance.product_id == product.id,
            StockBalance.location_id == location.id,
        )
    ).scalar_one()
    assert Decimal(after.quantity) == counted


def test_transfer_tenant_isolation(
    client: TestClient,
    admin_token: str,
    other_org_token: str,
) -> None:
    listing = client.get("/api/v1/stock/transfers", headers=_auth(admin_token))
    assert listing.status_code == 200
    # Other org cannot see primary transfers by id if any exist — create one briefly
    locs = client.get("/api/v1/locations", headers=_auth(admin_token))
    products = client.get("/api/v1/products?page=1&page_size=1", headers=_auth(admin_token))
    assert locs.status_code == 200 and products.status_code == 200
    loc_items = locs.json()
    prod_items = products.json()["items"]
    if len(loc_items) < 2 or not prod_items:
        return
    create = client.post(
        "/api/v1/stock/transfers",
        headers=_auth(admin_token),
        json={
            "source_location_id": loc_items[0]["id"],
            "destination_location_id": loc_items[1]["id"],
            "lines": [{"product_id": prod_items[0]["id"], "quantity": "1"}],
            "mark_in_transit": False,
        },
    )
    assert create.status_code == 201, create.text
    tid = create.json()["id"]
    other = client.get(f"/api/v1/stock/transfers/{tid}", headers=_auth(other_org_token))
    assert other.status_code == 404
