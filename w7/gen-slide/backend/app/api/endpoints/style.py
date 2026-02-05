"""Style API endpoints.

This module provides REST API endpoints for style generation and selection,
enabling users to customize the visual appearance of generated images.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Response
from app.models.api_schemas import GenerateStyleRequest, SelectStyleRequest
from app.models.slide import Style, SlidesProject
from app.services.slide_service import SlideService, SlideServiceError
from app.services.style_service import StyleService, StyleServiceError
from app.repositories.image_repository import ImageRepository, ImageRepositoryError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{slug}/style/generate")
async def generate_style(slug: str, request: GenerateStyleRequest) -> dict:
    """Generate style reference candidates from a text prompt.

    Args:
        slug: Project slug identifier
        request: Style generation request with prompt

    Returns:
        Dictionary with candidates array containing style options

    Raises:
        HTTPException: 404 if project not found, 500 if generation fails
    """
    import asyncio

    try:
        # Verify project exists
        slide_service = SlideService()
        project = slide_service.get_project(slug)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {slug} not found"
            )

        # Generate two style reference candidates in parallel
        style_service = StyleService()
        results = await asyncio.gather(
            style_service.generate_style(request.prompt),
            style_service.generate_style(request.prompt),
        )

        total_cost = sum(cost for _, cost in results)

        # Update total cost
        slide_service.update_total_cost(slug, total_cost)

        # Build candidates array with prompt and base64 image
        candidates = [
            {
                "image": f"data:image/png;base64,{base64_image}",
                "prompt": request.prompt
            }
            for base64_image, _ in results
        ]

        return {
            "candidates": candidates,
            "cost": total_cost,
            "message": "Style candidates generated successfully"
        }

    except SlideServiceError as e:
        logger.error(f"Slide service error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate style: {str(e)}"
        )
    except StyleServiceError as e:
        logger.error(f"Style service error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate style: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_style: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate style: {str(e)}"
        )


@router.post("/{slug}/style/select", response_model=SlidesProject)
async def select_style(slug: str, request: SelectStyleRequest) -> SlidesProject:
    """Select a style for the project.

    Args:
        slug: Project slug identifier
        request: Style selection request with prompt and image

    Returns:
        Updated SlidesProject with style configured

    Raises:
        HTTPException: 404 if project not found, 400 if validation fails
    """
    try:
        # Save style image to file system and create style object
        style_service = StyleService()
        style = style_service.save_style_image(slug, request.image)
        
        # Set the prompt in the style object
        style.prompt = request.prompt

        # Update project with style
        slide_service = SlideService()
        project = slide_service.update_style(slug, style)

        logger.info(f"Style selected for project {slug}: {request.prompt}")
        return project

    except StyleServiceError as e:
        if "Invalid" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        logger.error(f"Style service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except SlideServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Slide service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{slug}/style")
async def get_style_image(slug: str) -> Response:
    """Get the style image for a project.

    Args:
        slug: Project slug identifier

    Returns:
        JPEG image binary data

    Raises:
        HTTPException: 404 if project not found or no style set
    """
    try:
        slide_service = SlideService()
        project = slide_service.get_project(slug)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {slug} not found"
            )

        if not project.style:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No style set for project {slug}"
            )

        # Get style image from file system
        image_repo = ImageRepository()
        image_bytes = image_repo.get_style_image(slug)

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Style image file not found for project {slug}"
            )

        # Return image with caching headers
        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "Content-Disposition": 'inline; filename="style.jpg"'
            }
        )

    except SlideServiceError as e:
        logger.error(f"Slide service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except ImageRepositoryError as e:
        logger.error(f"Image repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
