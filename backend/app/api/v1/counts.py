"""Stock counts — thin create / submit / approve slice."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.permissions import CATALOG_ROLES, OPS_ROLES, require_roles
from app.schemas.count import (
    CountApproveRequest,
    CountApproveResponse,
    CountCreateRequest,
    CountDetail,
    CountSummary,
)
from app.schemas.pagination import Page
from app.services import counts as counts_service

router = APIRouter(prefix="/stock/counts", tags=["stock-counts"])


@router.get("", response_model=Page[CountSummary])
async def list_counts(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[CountSummary]:
    items = counts_service.list_counts(db, auth.organization_id)
    return Page(items=items, total=len(items), page=1, page_size=len(items) or 25)


@router.post("", response_model=CountDetail, status_code=201)
async def create_count(
    payload: CountCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CountDetail:
    require_roles(auth, OPS_ROLES, action="create stock counts")
    count = counts_service.create_count(db, auth, payload)
    count_id = count.id
    db.commit()
    count = counts_service.get_count(db, auth.organization_id, count_id)
    return counts_service.serialize_count(db, count)


@router.get("/{count_id}", response_model=CountDetail)
async def get_count(
    count_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CountDetail:
    count = counts_service.get_count(db, auth.organization_id, count_id)
    return counts_service.serialize_count(db, count)


@router.post("/{count_id}/submit", response_model=CountDetail)
async def submit_count(
    count_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CountDetail:
    require_roles(auth, OPS_ROLES, action="submit stock counts")
    counts_service.submit_count(db, auth, count_id)
    db.commit()
    count = counts_service.get_count(db, auth.organization_id, count_id)
    return counts_service.serialize_count(db, count)


@router.post("/{count_id}/approve", response_model=CountApproveResponse)
async def approve_count(
    count_id: uuid.UUID,
    payload: CountApproveRequest | None = None,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CountApproveResponse:
    # Approval is manager/owner gated (variance can change balances)
    require_roles(auth, CATALOG_ROLES, action="approve stock counts")
    result = counts_service.approve_count(
        db, auth, count_id, payload or CountApproveRequest()
    )
    db.commit()
    return result
