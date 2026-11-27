"""Versioned read-only Insights connector (Agent 5)."""

from __future__ import annotations

import hmac
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.session import get_db
from app.dependencies import get_current_settings
from app.errors import http_error
from app.models import Organization
from app.schemas.connector import ConnectorHealthResponse, InsightsSummaryResponse
from app.services import reports as reports_service

router = APIRouter(
    prefix="/connectors/insights/v1",
    tags=["connectors-insights"],
)


def _require_connector_auth(
    authorization: Annotated[str | None, Header()] = None,
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-Id")] = None,
    settings: Settings = Depends(get_current_settings),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    expected = (settings.insights_connector_token or "").strip()
    if not expected:
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "connector_disabled",
            "Insights connector token is not configured",
        )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "unauthorized",
            "Missing Bearer service token",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token or not hmac.compare_digest(token, expected):
        raise http_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_token",
            "Invalid Insights connector token",
        )

    if not x_organization_id:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "missing_organization",
            "X-Organization-Id header is required",
        )
    try:
        org_id = uuid.UUID(x_organization_id.strip())
    except ValueError as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_organization",
            "X-Organization-Id must be a UUID",
        ) from exc

    org = db.get(Organization, org_id)
    if org is None or org.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Organization not found")
    return org_id


@router.get("/health", response_model=ConnectorHealthResponse)
async def insights_health(
    _org_id: uuid.UUID = Depends(_require_connector_auth),
) -> ConnectorHealthResponse:
    return ConnectorHealthResponse()


@router.get("/summary", response_model=InsightsSummaryResponse)
async def insights_summary(
    org_id: uuid.UUID = Depends(_require_connector_auth),
    db: Session = Depends(get_db),
) -> InsightsSummaryResponse:
    dash = reports_service.dashboard_summary(db, org_id)
    report = reports_service.inventory_report(db, org_id, movement_limit=1)
    return InsightsSummaryResponse(
        generated_at=dash.generated_at,
        organization_id=str(org_id),
        inventory_value=dash.stock_value,
        low_stock_items=dash.low_stock_items,
        out_of_stock_items=dash.out_of_stock_items,
        pending_purchase_orders=dash.pending_purchase_orders,
        recent_movement_count=dash.recent_movement_count,
        product_count=dash.product_count,
        location_count=dash.location_count,
        balance_rows=report.balance_rows,
    )
