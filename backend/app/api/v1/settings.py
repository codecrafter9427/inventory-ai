"""Settings — org profile, roles (read), units, reorder defaults."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import Organization, Role, Unit
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.settings import (
    OrganizationSettings,
    OrganizationSettingsUpdate,
    RoleResponse,
    UnitCreate,
    UnitDetail,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/organization", response_model=OrganizationSettings)
async def get_organization_settings(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OrganizationSettings:
    org = db.get(Organization, auth.organization_id)
    if org is None or org.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Organization not found")
    return OrganizationSettings.model_validate(org)


@router.patch("/organization", response_model=OrganizationSettings)
async def update_organization_settings(
    body: OrganizationSettingsUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OrganizationSettings:
    require_roles(auth, frozenset({"owner"}), action="update organization settings")
    org = db.get(Organization, auth.organization_id)
    if org is None or org.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Organization not found")

    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(org, key, value)

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="settings.organization.update",
        entity_type="organization",
        entity_id=org.id,
        message="Updated organization settings",
        details=data,
    )
    db.commit()
    db.refresh(org)
    return OrganizationSettings.model_validate(org)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    rows = (
        db.query(Role)
        .filter(Role.organization_id == auth.organization_id)
        .order_by(Role.code.asc())
        .all()
    )
    return [RoleResponse.model_validate(r) for r in rows]


@router.get("/units", response_model=list[UnitDetail])
async def list_settings_units(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[UnitDetail]:
    rows = (
        db.query(Unit)
        .filter(Unit.organization_id == auth.organization_id)
        .order_by(Unit.code.asc())
        .all()
    )
    return [UnitDetail.model_validate(r) for r in rows]


@router.post("/units", response_model=UnitDetail, status_code=status.HTTP_201_CREATED)
async def create_unit(
    body: UnitCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UnitDetail:
    require_roles(auth, CATALOG_ROLES, action="create units")
    row = Unit(
        organization_id=auth.organization_id,
        code=body.code.strip().lower(),
        name=body.name.strip(),
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_unit",
            "Unit code already exists in this organization",
        ) from exc

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="settings.unit.create",
        entity_type="unit",
        entity_id=row.id,
        message=f"Created unit {row.code}",
        details={"code": row.code, "name": row.name},
    )
    db.commit()
    db.refresh(row)
    return UnitDetail.model_validate(row)
