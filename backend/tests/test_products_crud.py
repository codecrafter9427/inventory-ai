"""Product CRUD + search + tenant isolation API tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, Product, Unit


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_products_requires_auth(client: TestClient) -> None:
    res = client.get("/api/v1/products")
    assert res.status_code == 401


def test_list_and_search_products(client: TestClient, admin_token: str) -> None:
    res = client.get("/api/v1/products?page_size=10", headers=_auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 30
    assert len(body["items"]) >= 1
    assert "sku" in body["items"][0]

    search = client.get(
        "/api/v1/products?q=SKU-001",
        headers=_auth(admin_token),
    )
    assert search.status_code == 200
    items = search.json()["items"]
    assert any(p["sku"] == "SKU-001" for p in items)

    by_name = client.get(
        "/api/v1/products?q=Aurora",
        headers=_auth(admin_token),
    )
    assert by_name.status_code == 200
    assert any("Aurora" in p["name"] for p in by_name.json()["items"])

    by_barcode = client.get(
        "/api/v1/products?q=890100000001",
        headers=_auth(admin_token),
    )
    assert by_barcode.status_code == 200
    assert any(p.get("barcode") == "890100000001" for p in by_barcode.json()["items"])


def test_create_get_update_archive_product(
    client: TestClient,
    admin_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    unit = (
        db.query(Unit)
        .filter(Unit.organization_id == primary_org.id, Unit.code == "ea")
        .one()
    )
    sku = f"SKU-M2-{uuid.uuid4().hex[:8].upper()}"
    create = client.post(
        "/api/v1/products",
        headers=_auth(admin_token),
        json={
            "sku": sku,
            "name": "Milestone Two Widget",
            "barcode": f"99{uuid.uuid4().hex[:10]}",
            "unit_id": str(unit.id),
            "cost": "3.5000",
            "selling_price": "9.9900",
            "reorder_point": "5.0000",
        },
    )
    assert create.status_code == 201, create.text
    product = create.json()
    product_id = product["id"]
    assert product["sku"] == sku
    assert product["cost"] == "3.5000"

    got = client.get(f"/api/v1/products/{product_id}", headers=_auth(admin_token))
    assert got.status_code == 200
    assert got.json()["name"] == "Milestone Two Widget"

    patched = client.patch(
        f"/api/v1/products/{product_id}",
        headers=_auth(admin_token),
        json={"name": "Milestone Two Widget Updated", "selling_price": "11.5000"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Milestone Two Widget Updated"
    assert patched.json()["selling_price"] == "11.5000"

    deleted = client.delete(f"/api/v1/products/{product_id}", headers=_auth(admin_token))
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/products/{product_id}", headers=_auth(admin_token))
    assert missing.status_code == 404


def test_other_org_cannot_read_or_mutate_primary_product(
    client: TestClient,
    other_org_token: str,
    db: Session,
    primary_org: Organization,
) -> None:
    product = (
        db.query(Product)
        .filter(Product.organization_id == primary_org.id, Product.sku == "SKU-001")
        .one()
    )
    res = client.get(f"/api/v1/products/{product.id}", headers=_auth(other_org_token))
    assert res.status_code == 404

    patch = client.patch(
        f"/api/v1/products/{product.id}",
        headers=_auth(other_org_token),
        json={"name": "Hijacked"},
    )
    assert patch.status_code == 404

    # Other org list must not include primary SKUs
    listed = client.get("/api/v1/products", headers=_auth(other_org_token))
    assert listed.status_code == 200
    skus = {p["sku"] for p in listed.json()["items"]}
    assert "SKU-001" not in skus
    assert "OTHER-001" in skus


def test_staff_cannot_create_product(
    client: TestClient,
    db: Session,
    primary_org: Organization,
) -> None:
    login = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "staff@demo.inventory.local", "password": "demo-password"},
    )
    token = login.json()["access_token"]
    unit = (
        db.query(Unit)
        .filter(Unit.organization_id == primary_org.id, Unit.code == "ea")
        .one()
    )
    res = client.post(
        "/api/v1/products",
        headers=_auth(token),
        json={
            "sku": f"SKU-STAFF-{uuid.uuid4().hex[:6]}",
            "name": "Staff Attempt",
            "unit_id": str(unit.id),
            "cost": "1.00",
            "selling_price": "2.00",
        },
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden_role"
