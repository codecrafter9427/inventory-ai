"""Organization endpoints with server-side tenant scoping."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context, require_organization
from app.errors import http_error
from app.models import Organization
from app.schemas.common import OrganizationResponse
from fastapi import status

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    org = db.get(Organization, auth.organization_id)
    if org is None or org.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Organization not found")
    return OrganizationResponse(id=org.id, name=org.name, slug=org.slug)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    """Protected org lookup — wrong-org requests are denied with 403."""
    require_organization(organization_id, auth)
    org = db.get(Organization, organization_id)
    if org is None or org.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Organization not found")
    return OrganizationResponse(id=org.id, name=org.name, slug=org.slug)
