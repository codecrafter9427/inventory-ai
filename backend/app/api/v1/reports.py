"""Inventory reports + CSV export (deterministic)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.schemas.reports import DashboardSummary, InventoryReportSummary
from app.services import reports as reports_service

router = APIRouter(tags=["reports"])


@router.get("/reports/inventory", response_model=InventoryReportSummary)
async def get_inventory_report(
    movement_limit: int = Query(default=50, ge=1, le=200),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> InventoryReportSummary:
    return reports_service.inventory_report(
        db, auth.organization_id, movement_limit=movement_limit
    )


@router.get("/reports/inventory/stock-on-hand.csv")
async def export_stock_on_hand_csv(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Response:
    content = reports_service.stock_on_hand_csv(db, auth.organization_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="stock-on-hand.csv"'},
    )


@router.get("/reports/inventory/movements.csv")
async def export_movements_csv(
    limit: int = Query(default=500, ge=1, le=2000),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Response:
    content = reports_service.movements_csv(db, auth.organization_id, limit=limit)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="stock-movements.csv"'},
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    return reports_service.dashboard_summary(db, auth.organization_id)
