"""Aggregate /api/v1 routers."""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    auth,
    catalog,
    coming_soon,
    connectors,
    counts,
    locations,
    me,
    organizations,
    products,
    purchase_orders,
    receipts,
    reports,
    settings,
    stock,
    suppliers,
    transfers,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(organizations.router)
api_router.include_router(settings.router)
api_router.include_router(products.router)
api_router.include_router(catalog.router)
api_router.include_router(locations.router)
api_router.include_router(suppliers.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(receipts.router)
api_router.include_router(stock.router)
api_router.include_router(transfers.router)
api_router.include_router(counts.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router)
api_router.include_router(connectors.router)
# Coming Soon stubs last so implemented routes take precedence where paths overlap
api_router.include_router(coming_soon.router)
