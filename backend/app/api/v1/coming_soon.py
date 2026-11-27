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


@router.patch("/units/{item_id}")
@router.delete("/units/{item_id}")
async def units_item(
    item_id: str,
    _auth: AuthContext = Depends(get_auth_context),
) -> JSONResponse:
    return _soon("units")


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
