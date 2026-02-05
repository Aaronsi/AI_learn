"""FastAPI application entry point.

This module initializes the FastAPI application with middleware,
routers, and configuration for the GenSlides API.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting GenSlides API")
    logger.info(f"Slides base path: {settings.SLIDES_BASE_PATH}")

    # Ensure base directory exists
    from pathlib import Path
    path_str = settings.SLIDES_BASE_PATH
    # Resolve relative paths relative to backend directory
    if not Path(path_str).is_absolute():
        # Get backend directory (parent of app directory)
        backend_dir = Path(__file__).parent.parent.resolve()
        # Handle ../slides: go up one level from backend/ to w7/gen-slide/, then into slides/
        if path_str.startswith("../"):
            # Remove ../ prefix and resolve relative to backend's parent
            relative_path = path_str[3:]  # Remove "../"
            project_root = backend_dir.parent  # w7/gen-slide/
            base_path = (project_root / relative_path).resolve()
        else:
            # Relative path without .., resolve relative to backend/
            base_path = (backend_dir / path_str).resolve()
    else:
        base_path = Path(path_str).resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Resolved slides base path: {base_path}")

    yield

    # Shutdown
    logger.info("Shutting down GenSlides API")


# Create FastAPI application
app = FastAPI(
    title="GenSlides API",
    description="AI-powered slide image generator using Volcano Ark's Doubao-Seed-1.8 model",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    """Root endpoint.

    Returns:
        Welcome message and API information
    """
    return {
        "message": "GenSlides API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
