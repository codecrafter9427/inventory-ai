"""Aggregate /api/v1 routers."""

from fastapi import APIRouter

from app.api.v1 import ai, auth, coming_soon, me, organizations

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(organizations.router)
api_router.include_router(ai.router)
api_router.include_router(coming_soon.router)
