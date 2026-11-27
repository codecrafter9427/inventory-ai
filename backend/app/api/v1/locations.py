"""Location list + write API — organization-scoped."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import Location
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.location import LocationCreate, LocationDetail, LocationUpdate
from app.schemas.stock import LocationResponse
from app.services.audit import record_audit

router = APIRouter(prefix="/locations", tags=["locations"])


def _get_org_location(db: Session, auth: AuthContext, location_id: uuid.UUID) -> Location:
    row = (
        db.query(Location)
        .filter(Location.id == location_id, Location.organization_id == auth.organization_id)
        .one_or_none()
    )
    if row is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Location not found")
    return row


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    active_only: bool = Query(default=True),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[LocationResponse]:
    query = db.query(Location).filter(Location.organization_id == auth.organization_id)
    if active_only:
        query = query.filter(Location.is_active.is_(True))
    rows = query.order_by(Location.code.asc()).all()
    return [LocationResponse.model_validate(r) for r in rows]


@router.post("", response_model=LocationDetail, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LocationDetail:
    require_roles(auth, CATALOG_ROLES, action="create locations")
    row = Location(
        organization_id=auth.organization_id,
        code=body.code.strip().upper(),
        name=body.name.strip(),
        address=body.address,
        bin_shelf_notes=body.bin_shelf_notes,
        is_active=body.is_active,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_location",
            "Location code already exists in this organization",
        ) from exc

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="location.create",
        entity_type="location",
        entity_id=row.id,
        message=f"Created location {row.code}",
        details={"code": row.code, "name": row.name},
    )
    db.commit()
    db.refresh(row)
    return LocationDetail.model_validate(row)


@router.get("/{location_id}", response_model=LocationDetail)
async def get_location(
    location_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LocationDetail:
    return LocationDetail.model_validate(_get_org_location(db, auth, location_id))


@router.patch("/{location_id}", response_model=LocationDetail)
async def update_location(
    location_id: uuid.UUID,
    body: LocationUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LocationDetail:
    require_roles(auth, CATALOG_ROLES, action="update locations")
    row = _get_org_location(db, auth, location_id)
    data = body.model_dump(exclude_unset=True)
    if "code" in data and data["code"] is not None:
        data["code"] = data["code"].strip().upper()
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
            "duplicate_location",
            "Location code already exists in this organization",
        ) from exc

    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="location.update",
        entity_type="location",
        entity_id=row.id,
        message=f"Updated location {row.code}",
        details=data,
    )
    db.commit()
    db.refresh(row)
    return LocationDetail.model_validate(row)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_location(
    location_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    require_roles(auth, CATALOG_ROLES, action="deactivate locations")
    row = _get_org_location(db, auth, location_id)
    row.is_active = False
    record_audit(
        db,
        organization_id=auth.organization_id,
        actor_user_id=auth.user_id,
        action="location.deactivate",
        entity_type="location",
        entity_id=row.id,
        message=f"Deactivated location {row.code}",
    )
    db.commit()
