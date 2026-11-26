"""Pytest fixtures for Inventory AI API smoke tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app
from app.models import Organization


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def primary_org(db: Session) -> Organization:
    return db.query(Organization).filter(Organization.slug == "demo-retail").one()


@pytest.fixture
def secondary_org(db: Session) -> Organization:
    return db.query(Organization).filter(Organization.slug == "other-demo").one()


@pytest.fixture
def admin_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "admin@demo.inventory.local", "password": "demo-password"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def other_org_token(client: TestClient) -> str:
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "other@demo.inventory.local", "password": "demo-password"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
