"""Supplier directory CRUD — organization-scoped."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import Supplier
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _to_response(row: Supplier) -> SupplierResponse:
    return SupplierResponse.model_validate(row)


def _get_org_supplier(db: Session, auth: AuthContext, supplier_id: uuid.UUID) -> Supplier:
    row = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.organization_id == auth.organization_id)
        .one_or_none()
    )
    if row is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Supplier not found")
    return row


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    active_only: bool = Query(default=True),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[SupplierResponse]:
    query = db.query(Supplier).filter(Supplier.organization_id == auth.organization_id)
    if active_only:
        query = query.filter(Supplier.is_active.is_(True))
    rows = query.order_by(Supplier.name.asc()).all()
    return [_to_response(r) for r in rows]


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    body: SupplierCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SupplierResponse:
    require_roles(auth, CATALOG_ROLES, action="create suppliers")
    row = Supplier(
        organization_id=auth.organization_id,
        name=body.name.strip(),
        email=body.email,
        phone=body.phone,
        lead_time_days=body.lead_time_days,
        notes=body.notes,
        is_active=body.is_active,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_supplier",
            "Supplier name already exists in this organization",
        ) from exc

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="supplier.create",
        entity_type="supplier",
        entity_id=row.id,
        message=f"Created supplier {row.name}",
        details={"name": row.name, "lead_time_days": row.lead_time_days},
    )
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SupplierResponse:
    return _to_response(_get_org_supplier(db, auth, supplier_id))


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    body: SupplierUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SupplierResponse:
    require_roles(auth, CATALOG_ROLES, action="update suppliers")
    row = _get_org_supplier(db, auth, supplier_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(row, key, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_supplier",
            "Supplier name already exists in this organization",
        ) from exc

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="supplier.update",
        entity_type="supplier",
        entity_id=row.id,
        message=f"Updated supplier {row.name}",
        details=data,
    )
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_supplier(
    supplier_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    """Soft-deactivate (is_active=false) — preserves PO history."""
    require_roles(auth, CATALOG_ROLES, action="deactivate suppliers")
    row = _get_org_supplier(db, auth, supplier_id)
    row.is_active = False
    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="supplier.deactivate",
        entity_type="supplier",
        entity_id=row.id,
        message=f"Deactivated supplier {row.name}",
    )
    db.commit()
