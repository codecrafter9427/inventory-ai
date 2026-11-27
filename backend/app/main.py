"""Inventory AI FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.errors import http_exception_handler, validation_exception_handler
from app.schemas.common import HealthResponse

settings = get_settings()

app = FastAPI(
    title="Inventory AI",
    description=(
        "Stock and warehouse operations MVP (portfolio) — Milestone 6: "
        "suppliers/locations/settings, PO write, ledger integrity, Insights connector."
    ),
    version=__version__,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)
