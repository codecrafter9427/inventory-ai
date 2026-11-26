"""Auth + organization tenant isolation smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Location, Organization, Product, PurchaseOrder, Role, Supplier, User


def test_demo_login_owner(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "admin@demo.inventory.local", "password": "demo-password"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "owner"
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["organization_id"]


def test_demo_login_manager_and_staff(client: TestClient) -> None:
    manager = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "manager@demo.inventory.local", "password": "demo-password"},
    )
    staff = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "staff@demo.inventory.local", "password": "demo-password"},
    )
    assert manager.status_code == 200
    assert staff.status_code == 200
    assert manager.json()["role"] == "inventory_manager"
    assert staff.json()["role"] == "staff"


def test_demo_login_invalid_credentials(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "admin@demo.inventory.local", "password": "wrong-password"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "invalid_credentials"


def test_me_requires_auth(client: TestClient) -> None:
    res = client.get("/api/v1/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "unauthorized"


def test_me_returns_current_user(client: TestClient, admin_token: str) -> None:
    res = client.get("/api/v1/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "admin@demo.inventory.local"
    assert body["role"] == "owner"
    assert body["organization_slug"] == "demo-retail"


def test_current_organization(client: TestClient, admin_token: str) -> None:
    res = client.get(
        "/api/v1/organizations/current",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["slug"] == "demo-retail"


def test_wrong_org_access_denied(
    client: TestClient,
    admin_token: str,
    secondary_org: Organization,
) -> None:
    res = client.get(
        f"/api/v1/organizations/{secondary_org.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 403
    body = res.json()
    assert body["error"]["code"] == "forbidden_organization"


def test_own_org_access_allowed(
    client: TestClient,
    admin_token: str,
    primary_org: Organization,
) -> None:
    res = client.get(
        f"/api/v1/organizations/{primary_org.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["id"] == str(primary_org.id)


def test_other_org_cannot_read_primary(
    client: TestClient,
    other_org_token: str,
    primary_org: Organization,
) -> None:
    res = client.get(
        f"/api/v1/organizations/{primary_org.id}",
        headers={"Authorization": f"Bearer {other_org_token}"},
    )
    assert res.status_code == 403


def test_seed_minimums(db: Session, primary_org: Organization) -> None:
    products = db.query(Product).filter(Product.organization_id == primary_org.id).count()
    locations = db.query(Location).filter(Location.organization_id == primary_org.id).count()
    suppliers = db.query(Supplier).filter(Supplier.organization_id == primary_org.id).count()
    pos = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.organization_id == primary_org.id)
        .count()
    )
    roles = db.query(Role).filter(Role.organization_id == primary_org.id).count()
    users = db.query(User).filter(User.organization_id == primary_org.id).count()

    assert products >= 30
    assert locations >= 3
    assert suppliers >= 5
    assert pos >= 8
    assert roles >= 3
    assert users >= 3


def test_protected_products_require_auth(client: TestClient) -> None:
    res = client.get("/api/v1/products")
    assert res.status_code == 401
