"""Location list (read) for stock filters and forms."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.models import Location
from app.schemas.stock import LocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[LocationResponse]:
    rows = (
        db.query(Location)
        .filter(
            Location.organization_id == auth.organization_id,
            Location.is_active.is_(True),
        )
        .order_by(Location.code.asc())
        .all()
    )
    return [LocationResponse.model_validate(r) for r in rows]
