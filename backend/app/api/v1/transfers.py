"""Stock transfers — thin create / list / receive slice."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.permissions import OPS_ROLES, require_roles
from app.schemas.pagination import Page
from app.schemas.transfer import (
    TransferCreateRequest,
    TransferDetail,
    TransferReceiveResponse,
    TransferSummary,
)
from app.services import transfers as transfers_service

router = APIRouter(prefix="/stock/transfers", tags=["stock-transfers"])


@router.get("", response_model=Page[TransferSummary])
async def list_transfers(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[TransferSummary]:
    items = transfers_service.list_transfers(db, auth.organization_id)
    return Page(items=items, total=len(items), page=1, page_size=len(items) or 25)


@router.post("", response_model=TransferDetail, status_code=201)
async def create_transfer(
    payload: TransferCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TransferDetail:
    require_roles(auth, OPS_ROLES, action="create stock transfers")
    transfer = transfers_service.create_transfer(db, auth, payload)
    transfer_id = transfer.id
    db.commit()
    transfer = transfers_service.get_transfer(db, auth.organization_id, transfer_id)
    return transfers_service.serialize_transfer(db, transfer)


@router.get("/{transfer_id}", response_model=TransferDetail)
async def get_transfer(
    transfer_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TransferDetail:
    transfer = transfers_service.get_transfer(db, auth.organization_id, transfer_id)
    return transfers_service.serialize_transfer(db, transfer)


@router.post("/{transfer_id}/receive", response_model=TransferReceiveResponse)
async def receive_transfer(
    transfer_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TransferReceiveResponse:
    require_roles(auth, OPS_ROLES, action="receive stock transfers")
    result = transfers_service.receive_transfer(db, auth, transfer_id)
    db.commit()
    return result
