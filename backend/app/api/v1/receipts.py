"""PO receiving — atomic StockBalance + StockMovement updates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.permissions import OPS_ROLES, require_roles
from app.schemas.purchase_order import ReceiveRequest, ReceiveResponse
from app.services.receiving import receive_purchase_order

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("", response_model=ReceiveResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
    body: ReceiveRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ReceiveResponse:
    """
    Receive against a purchase order.

    Updates balances and appends immutable ledger rows in a single DB transaction.
    Org scoping is enforced inside the service (wrong-org PO → 404).
    """
    require_roles(auth, OPS_ROLES, action="receive purchase orders")
    result = receive_purchase_order(db, auth, body)
    db.commit()
    return result
