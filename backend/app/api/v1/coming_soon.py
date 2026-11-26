"""Coming Soon stubs for remaining Inventory AI API groups (auth required)."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.dependencies import AuthContext, get_auth_context
from app.schemas.common import ComingSoonResponse

router = APIRouter(tags=["coming-soon"])


def _soon(feature: str) -> JSONResponse:
    body = ComingSoonResponse(feature=feature)
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=body.model_dump(),
    )


@router.post("/categories")
async def categories_create(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("categories")


@router.get("/categories/{item_id}")
@router.patch("/categories/{item_id}")
@router.delete("/categories/{item_id}")
async def categories_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("categories")


@router.post("/units")
async def units_create(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("units")


@router.get("/units/{item_id}")
@router.patch("/units/{item_id}")
@router.delete("/units/{item_id}")
async def units_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("units")


@router.post("/locations")
async def locations_create(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("locations")


@router.get("/locations/{item_id}")
@router.patch("/locations/{item_id}")
@router.delete("/locations/{item_id}")
async def locations_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("locations")


@router.get("/suppliers")
@router.post("/suppliers")
async def suppliers_collection(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("suppliers")


@router.get("/suppliers/{item_id}")
@router.patch("/suppliers/{item_id}")
@router.delete("/suppliers/{item_id}")
async def suppliers_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("suppliers")


@router.post("/purchase-orders")
async def purchase_orders_create(
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("purchase-orders-write")


@router.patch("/purchase-orders/{item_id}")
@router.delete("/purchase-orders/{item_id}")
async def purchase_orders_mutate(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("purchase-orders-write")


@router.get("/receipts")
@router.get("/receipts/{item_id}")
@router.patch("/receipts/{item_id}")
async def receipts_read(
    item_id: str | None = None,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("receipts-history")


@router.post("/stock/movements")
async def stock_movements_write(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("stock/movements-adjust")


@router.get("/stock/counts")
@router.post("/stock/counts")
async def stock_counts_collection(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("stock/counts")


@router.get("/stock/counts/{item_id}")
@router.patch("/stock/counts/{item_id}")
async def stock_counts_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("stock/counts")


@router.get("/stock/transfers")
@router.post("/stock/transfers")
async def stock_transfers_collection(
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("stock/transfers")


@router.get("/stock/transfers/{item_id}")
@router.patch("/stock/transfers/{item_id}")
async def stock_transfers_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("stock/transfers")


@router.get("/reports/inventory")
async def reports_inventory(_auth: AuthContext = Depends(get_auth_context)) -> JSONResponse:
    return _soon("reports/inventory")
