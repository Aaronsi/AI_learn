"""Image API endpoints.

This module provides REST API endpoints for image generation and retrieval,
including content-based caching and image serving.
"""

import base64
import logging
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from typing import List
from app.models.api_schemas import GenerateImageResponse
from app.services.slide_service import SlideService, SlideServiceError
from app.services.image_service import ImageService, ImageServiceError
from app.repositories.image_repository import ImageRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{slug}/generate/{sid}", response_model=GenerateImageResponse)
async def generate_image(slug: str, sid: str) -> GenerateImageResponse:
    """Generate an image for a slide.

    This endpoint generates an image based on the slide's current content.
    If an image already exists for the current content hash, it returns
    the cached version with zero cost.

    Args:
        slug: Project slug identifier
        sid: Slide identifier

    Returns:
        GenerateImageResponse with image hash and cost

    Raises:
        HTTPException: 404 if project or slide not found, 500 if generation fails
    """
    try:
        # Get slide content and style
        slide_service = SlideService()
        project = slide_service.get_project(slug)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {slug} not found"
            )

        # Find the slide
        slide = None
        for s in project.slides:
            if s.sid == sid:
                slide = s
                break

        if not slide:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slide {sid} not found in project {slug}"
            )

        # Generate image
        image_service = ImageService()
        style_prompt = project.style.prompt if project.style else None

        # Read style image and convert to base64 if it exists
        style_image_base64 = None
        if project.style and project.style.image:
            image_repo = ImageRepository()
            style_image_bytes = image_repo.get_style_image(slug)
            if style_image_bytes:
                style_image_base64 = base64.b64encode(style_image_bytes).decode('utf-8')

        image_hash, cost = await image_service.generate_image_for_slide(
            slug=slug,
            sid=sid,
            content=slide.content,
            style_prompt=style_prompt,
            style_image=style_image_base64
        )

        # Update total cost if generation occurred
        if cost > 0:
            slide_service.update_total_cost(slug, cost)

        message = "Image generated successfully" if cost > 0 else "Using cached image"

        return GenerateImageResponse(
            image_hash=image_hash,
            cost=cost,
            message=message
        )

    except SlideServiceError as e:
        logger.error(f"Slide service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except ImageServiceError as e:
        logger.error(f"Image service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{slug}/images/{sid}", response_model=List[str])
async def list_images(slug: str, sid: str) -> List[str]:
    """List all image hashes for a slide.

    Args:
        slug: Project slug identifier
        sid: Slide identifier

    Returns:
        List of image hashes

    Raises:
        HTTPException: 500 if listing fails
    """
    try:
        image_service = ImageService()
        image_hashes = image_service.list_images_for_slide(slug, sid)
        return image_hashes

    except ImageServiceError as e:
        logger.error(f"Error listing images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{slug}/images/{sid}/{image_hash}.jpg")
async def get_image(slug: str, sid: str, image_hash: str) -> Response:
    """Get an image by hash.

    Args:
        slug: Project slug identifier
        sid: Slide identifier
        image_hash: Blake3 hash of the image (without .jpg extension)

    Returns:
        JPEG image with appropriate caching headers

    Raises:
        HTTPException: 404 if image not found
    """
    try:
        image_service = ImageService()
        image_bytes = image_service.get_image(slug, sid, image_hash)

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image {image_hash} not found for slide {sid}"
            )

        # Return image with caching headers
        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "Content-Disposition": f'inline; filename="{image_hash}.jpg"'
            }
        )

    except ImageServiceError as e:
        logger.error(f"Error getting image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
