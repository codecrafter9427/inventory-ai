"""Milestone 6 — suppliers/locations/settings, PO write, ledger, connector, hardening."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    AuditEvent,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    StockBalance,
    StockMovement,
    Supplier,
    Unit,
)
from app.services.ledger import verify_ledger_integrity
from app.services.rate_limit import login_rate_limiter


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "staff@demo.inventory.local", "password": "demo-password"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def manager_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "manager@demo.inventory.local", "password": "demo-password"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


# --- Ledger integrity -------------------------------------------------------


def test_ledger_integrity_balance_equals_sum_movements(
    db: Session,
    primary_org: Organization,
) -> None:
    """Isolated product/location — balance must equal sum(movements)."""
    unit = db.query(Unit).filter(Unit.organization_id == primary_org.id).first()
    location = db.query(Location).filter(Location.organization_id == primary_org.id).first()
    assert unit and location
    product = Product(
        organization_id=primary_org.id,
        sku=f"LEDGER-{uuid.uuid4().hex[:8].upper()}",
        name="Ledger Integrity Widget",
        unit_id=unit.id,
        cost=Decimal("1"),
        selling_price=Decimal("2"),
        reorder_point=Decimal("0"),
        safety_stock=Decimal("0"),
        lead_time_days=7,
        is_active=True,
    )
    db.add(product)
    db.flush()

    open_qty = Decimal("10.0000")
    recv_qty = Decimal("3.0000")
    bal = StockBalance(
        organization_id=primary_org.id,
        product_id=product.id,
        location_id=location.id,
        quantity=open_qty + recv_qty,
    )
    db.add(bal)
    db.add(
        StockMovement(
            organization_id=primary_org.id,
            product_id=product.id,
            location_id=location.id,
            movement_type="opening",
            quantity=open_qty,
            balance_after=open_qty,
            reason="test opening",
        )
    )
    db.add(
        StockMovement(
            organization_id=primary_org.id,
            product_id=product.id,
            location_id=location.id,
            movement_type="receive",
            quantity=recv_qty,
            balance_after=open_qty + recv_qty,
            reason="test receive",
        )
    )
    db.commit()

    report = verify_ledger_integrity(
        db,
        primary_org.id,
        product_id=product.id,
        location_id=location.id,
    )
    assert report.ok, [(m.delta, m.balance_quantity, m.movements_sum) for m in report.mismatches]
    assert report.balance_rows == 1


def test_ledger_integrity_detects_mismatch(
    db: Session,
    primary_org: Organization,
) -> None:
    unit = db.query(Unit).filter(Unit.organization_id == primary_org.id).first()
    location = db.query(Location).filter(Location.organization_id == primary_org.id).first()
    product = Product(
        organization_id=primary_org.id,
        sku=f"MISMATCH-{uuid.uuid4().hex[:8].upper()}",
        name="Ledger Mismatch Widget",
        unit_id=unit.id,
        cost=Decimal("1"),
        selling_price=Decimal("2"),
        reorder_point=Decimal("0"),
        safety_stock=Decimal("0"),
        lead_time_days=7,
        is_active=True,
    )
    db.add(product)
    db.flush()
    bal = StockBalance(
        organization_id=primary_org.id,
        product_id=product.id,
        location_id=location.id,
        quantity=Decimal("5.0000"),
    )
    db.add(bal)
    db.add(
        StockMovement(
            organization_id=primary_org.id,
            product_id=product.id,
            location_id=location.id,
            movement_type="opening",
            quantity=Decimal("5.0000"),
            balance_after=Decimal("5.0000"),
            reason="test opening",
        )
    )
    db.commit()

    bal = (
        db.query(StockBalance)
        .filter(
            StockBalance.product_id == product.id,
            StockBalance.location_id == location.id,
        )
        .one()
    )
    bal.quantity = bal.quantity + Decimal("99.0000")
    db.flush()
    try:
        report = verify_ledger_integrity(
            db,
            primary_org.id,
            product_id=product.id,
            location_id=location.id,
        )
        assert not report.ok
        assert any(m.delta == Decimal("99.0000") for m in report.mismatches)
    finally:
        bal.quantity = Decimal("5.0000")
        db.commit()


# --- Suppliers / locations / settings ---------------------------------------


def test_supplier_create_update_org_isolation(
    client: TestClient,
    admin_token: str,
    other_org_token: str,
    staff_token: str,
) -> None:
    name = f"Supplier-{uuid.uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/suppliers",
        headers=_auth(admin_token),
        json={"name": name, "lead_time_days": 5, "email": "s@example.com"},
    )
    assert created.status_code == 201, created.text
    sid = created.json()["id"]

    listed = client.get("/api/v1/suppliers", headers=_auth(admin_token))
    assert listed.status_code == 200
    assert any(s["id"] == sid for s in listed.json())

    # Other org cannot see
    other_list = client.get("/api/v1/suppliers", headers=_auth(other_org_token))
    assert other_list.status_code == 200
    assert all(s["id"] != sid for s in other_list.json())

    other_get = client.get(f"/api/v1/suppliers/{sid}", headers=_auth(other_org_token))
    assert other_get.status_code == 404

    # Staff cannot create
    denied = client.post(
        "/api/v1/suppliers",
        headers=_auth(staff_token),
        json={"name": f"Staff-{uuid.uuid4().hex[:6]}", "lead_time_days": 3},
    )
    assert denied.status_code == 403

    patched = client.patch(
        f"/api/v1/suppliers/{sid}",
        headers=_auth(admin_token),
        json={"lead_time_days": 9},
    )
    assert patched.status_code == 200
    assert patched.json()["lead_time_days"] == 9


def test_location_create_org_isolation(
    client: TestClient,
    admin_token: str,
    other_org_token: str,
    staff_token: str,
) -> None:
    code = f"L{uuid.uuid4().hex[:6].upper()}"
    created = client.post(
        "/api/v1/locations",
        headers=_auth(admin_token),
        json={"code": code, "name": "Test Bay"},
    )
    assert created.status_code == 201, created.text
    lid = created.json()["id"]

    other = client.get(f"/api/v1/locations/{lid}", headers=_auth(other_org_token))
    assert other.status_code == 404

    staff_denied = client.post(
        "/api/v1/locations",
        headers=_auth(staff_token),
        json={"code": f"S{uuid.uuid4().hex[:5].upper()}", "name": "Staff Loc"},
    )
    assert staff_denied.status_code == 403


def test_settings_org_roles_units(
    client: TestClient,
    admin_token: str,
    manager_token: str,
    staff_token: str,
) -> None:
    org = client.get("/api/v1/settings/organization", headers=_auth(admin_token))
    assert org.status_code == 200
    assert "default_reorder_point" in org.json()
    assert "default_lead_time_days" in org.json()

    roles = client.get("/api/v1/settings/roles", headers=_auth(admin_token))
    assert roles.status_code == 200
    codes = {r["code"] for r in roles.json()}
    assert {"owner", "inventory_manager", "staff"} <= codes

    # Owner can update reorder defaults
    patched = client.patch(
        "/api/v1/settings/organization",
        headers=_auth(admin_token),
        json={"default_reorder_point": "3.0000", "default_lead_time_days": 5},
    )
    assert patched.status_code == 200
    assert patched.json()["default_lead_time_days"] == 5

    # Manager cannot update org settings
    mgr = client.patch(
        "/api/v1/settings/organization",
        headers=_auth(manager_token),
        json={"default_lead_time_days": 8},
    )
    assert mgr.status_code == 403

    # Manager can create units
    unit_code = f"u{uuid.uuid4().hex[:5]}"
    unit = client.post(
        "/api/v1/settings/units",
        headers=_auth(manager_token),
        json={"code": unit_code, "name": "Test Unit"},
    )
    assert unit.status_code == 201, unit.text

    staff_unit = client.post(
        "/api/v1/settings/units",
        headers=_auth(staff_token),
        json={"code": f"x{uuid.uuid4().hex[:5]}", "name": "Nope"},
    )
    assert staff_unit.status_code == 403


# --- PO write lifecycle -----------------------------------------------------


def test_po_create_edit_submit_cancel_and_receive(
    client: TestClient,
    admin_token: str,
    staff_token: str,
    other_org_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    supplier = db.query(Supplier).filter(Supplier.organization_id == primary_org.id).first()
    location = db.query(Location).filter(Location.organization_id == primary_org.id).first()
    product = (
        db.query(Product)
        .filter(Product.organization_id == primary_org.id, Product.archived_at.is_(None))
        .first()
    )
    assert supplier and location and product

    # Staff cannot create
    staff_create = client.post(
        "/api/v1/purchase-orders",
        headers=_auth(staff_token),
        json={
            "supplier_id": str(supplier.id),
            "location_id": str(location.id),
            "lines": [{"product_id": str(product.id), "quantity_ordered": "4"}],
        },
    )
    assert staff_create.status_code == 403

    create = client.post(
        "/api/v1/purchase-orders",
        headers=_auth(admin_token),
        json={
            "supplier_id": str(supplier.id),
            "location_id": str(location.id),
            "notes": "M6 test PO",
            "lines": [{"product_id": str(product.id), "quantity_ordered": "5.0000"}],
        },
    )
    assert create.status_code == 201, create.text
    po = create.json()
    po_id = po["id"]
    assert po["status"] == "draft"

    # Other org isolation
    other = client.get(f"/api/v1/purchase-orders/{po_id}", headers=_auth(other_org_token))
    assert other.status_code == 404

    edit = client.patch(
        f"/api/v1/purchase-orders/{po_id}",
        headers=_auth(admin_token),
        json={
            "notes": "M6 edited",
            "lines": [{"product_id": str(product.id), "quantity_ordered": "3.0000"}],
        },
    )
    assert edit.status_code == 200
    assert edit.json()["notes"] == "M6 edited"
    assert edit.json()["lines"][0]["quantity_ordered"] == "3.0000"

    submit = client.post(
        f"/api/v1/purchase-orders/{po_id}/submit",
        headers=_auth(admin_token),
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == "ordered"
    assert submit.json()["ordered_at"] is not None

    # Audit on submit
    audits = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.organization_id == primary_org.id,
            AuditEvent.entity_id == uuid.UUID(po_id),
            AuditEvent.action == "purchase_order.submit",
        )
        .all()
    )
    assert len(audits) >= 1

    # Staff can receive
    line_id = submit.json()["lines"][0]["id"]
    recv = client.post(
        "/api/v1/receipts",
        headers=_auth(staff_token),
        json={
            "purchase_order_id": po_id,
            "lines": [{"purchase_order_line_id": line_id, "quantity": "1.0000"}],
        },
    )
    assert recv.status_code == 201, recv.text
    assert recv.json()["status"] in {"partially_received", "received"}

    # Cancel blocked after receive
    cancel_blocked = client.post(
        f"/api/v1/purchase-orders/{po_id}/cancel",
        headers=_auth(admin_token),
    )
    assert cancel_blocked.status_code == 409

    # Fresh PO to cancel
    create2 = client.post(
        "/api/v1/purchase-orders",
        headers=_auth(admin_token),
        json={
            "supplier_id": str(supplier.id),
            "location_id": str(location.id),
            "lines": [{"product_id": str(product.id), "quantity_ordered": "2"}],
        },
    )
    po2 = create2.json()["id"]
    cancel = client.post(
        f"/api/v1/purchase-orders/{po2}/cancel",
        headers=_auth(admin_token),
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"


def test_receive_audit_event(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    from datetime import datetime, timezone

    from app.models import PurchaseOrderLine

    supplier = db.query(Supplier).filter(Supplier.organization_id == primary_org.id).first()
    location = db.query(Location).filter(Location.organization_id == primary_org.id).first()
    product = (
        db.query(Product)
        .filter(Product.organization_id == primary_org.id, Product.archived_at.is_(None))
        .first()
    )
    po = PurchaseOrder(
        organization_id=primary_org.id,
        supplier_id=supplier.id,
        location_id=location.id,
        po_number=f"PO-AUD-{uuid.uuid4().hex[:6].upper()}",
        status="ordered",
        ordered_at=datetime.now(timezone.utc),
    )
    db.add(po)
    db.flush()
    line = PurchaseOrderLine(
        purchase_order_id=po.id,
        product_id=product.id,
        quantity_ordered=Decimal("2"),
        quantity_received=Decimal("0"),
        unit_cost=product.cost,
    )
    db.add(line)
    db.commit()

    res = client.post(
        "/api/v1/receipts",
        headers=_auth(admin_token),
        json={
            "purchase_order_id": str(po.id),
            "lines": [{"purchase_order_line_id": str(line.id), "quantity": "1"}],
        },
    )
    assert res.status_code == 201, res.text

    db.expire_all()
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_id == po.id,
            AuditEvent.action == "purchase_order.receive",
        )
        .all()
    )
    assert len(events) >= 1


# --- Insights connector -----------------------------------------------------


def test_insights_connector_summary(
    client: TestClient,
    primary_org: Organization,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "test-insights-connector-token"
    monkeypatch.setenv("INSIGHTS_CONNECTOR_TOKEN", token)
    get_settings.cache_clear()

    try:
        bad = client.get("/api/v1/connectors/insights/v1/health")
        assert bad.status_code == 401

        health = client.get(
            "/api/v1/connectors/insights/v1/health",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(primary_org.id),
            },
        )
        assert health.status_code == 200
        assert health.json()["connector"] == "insights"

        summary = client.get(
            "/api/v1/connectors/insights/v1/summary",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Organization-Id": str(primary_org.id),
            },
        )
        assert summary.status_code == 200, summary.text
        body = summary.json()
        assert body["organization_id"] == str(primary_org.id)
        assert "inventory_value" in body
        assert "low_stock_items" in body
        assert "pending_purchase_orders" in body
        assert body["product_count"] >= 30
    finally:
        monkeypatch.delenv("INSIGHTS_CONNECTOR_TOKEN", raising=False)
        get_settings.cache_clear()


# --- Login rate limit -------------------------------------------------------


def test_login_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Use a dedicated email so fixture logins for admin/staff are not blocked.
    # Auth handler syncs max_calls from settings each request — patch settings.
    email = "rate-limit-probe@demo.inventory.local"
    monkeypatch.setenv("LOGIN_RATE_LIMIT_PER_MINUTE", "3")
    get_settings.cache_clear()
    login_rate_limiter.reset()
    try:
        last = None
        for _ in range(4):
            last = client.post(
                "/api/v1/auth/demo-login",
                json={"email": email, "password": "wrong-password"},
            )
        assert last is not None
        assert last.status_code == 429
        assert last.json()["error"]["code"] == "rate_limited"
    finally:
        monkeypatch.delenv("LOGIN_RATE_LIMIT_PER_MINUTE", raising=False)
        get_settings.cache_clear()
        login_rate_limiter.reset()
