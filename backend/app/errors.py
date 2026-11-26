"""Consistent API error helpers: {error:{code,message,details}}."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


def http_error(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_body(code, message, details))


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        content = detail
    elif isinstance(detail, dict) and {"code", "message"} <= detail.keys():
        content = {"error": detail}
    else:
        content = error_body("http_error", str(detail))
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_body("validation_error", "Request validation failed", exc.errors()),
    )
