"""API router aggregation.

This module aggregates all API endpoint routers and provides
a single router for the main application to include.
"""

from fastapi import APIRouter
from app.api.endpoints import slides, images, style

# Create main API router
api_router = APIRouter()

# Include endpoint routers with appropriate prefixes and tags
api_router.include_router(
    slides.router,
    prefix="/slides",
    tags=["slides"]
)

api_router.include_router(
    images.router,
    prefix="/slides",
    tags=["images"]
)

api_router.include_router(
    style.router,
    prefix="/slides",
    tags=["style"]
)
