"""Slide API endpoints.

This module provides REST API endpoints for slide project management,
including CRUD operations and cost tracking.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.models.api_schemas import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ReorderSlidesRequest,
    CreateSlideRequest,
    UpdateSlideRequest,
    CostResponse,
)
from app.models.slide import SlidesProject, Slide
from app.services.slide_service import SlideService, SlideServiceError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{slug}", response_model=SlidesProject)
async def get_project(slug: str) -> SlidesProject:
    """Get a slide project by slug.

    Args:
        slug: Project slug identifier

    Returns:
        SlidesProject with computed image metadata

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        service = SlideService()
        project = service.get_project(slug)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {slug} not found"
            )

        return project

    except SlideServiceError as e:
        logger.error(f"Error getting project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{slug}", response_model=SlidesProject, status_code=status.HTTP_201_CREATED)
async def create_project(slug: str, request: CreateProjectRequest) -> SlidesProject:
    """Create a new slide project.

    Args:
        slug: Project slug identifier (must match request.slug)
        request: Project creation request

    Returns:
        Created SlidesProject

    Raises:
        HTTPException: 400 if slug mismatch, 409 if project exists
    """
    if slug != request.slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug in URL must match slug in request body"
        )

    try:
        service = SlideService()
        project = service.create_project(request.slug, request.title)
        return project

    except SlideServiceError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        logger.error(f"Error creating project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{slug}", response_model=SlidesProject)
async def update_project(slug: str, request: UpdateProjectRequest) -> SlidesProject:
    """Update a project's title.

    Args:
        slug: Project slug identifier
        request: Project update request

    Returns:
        Updated SlidesProject

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        service = SlideService()
        project = service.update_project_title(slug, request.title)
        return project

    except SlideServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Error updating project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{slug}/reorder", response_model=SlidesProject)
async def reorder_slides(slug: str, request: ReorderSlidesRequest) -> SlidesProject:
    """Reorder slides in a project.

    Args:
        slug: Project slug identifier
        request: Reorder request with ordered slide IDs

    Returns:
        Updated SlidesProject

    Raises:
        HTTPException: 404 if project not found, 400 if slide IDs invalid
    """
    try:
        service = SlideService()
        project = service.reorder_slides(slug, request.slide_ids)
        return project

    except SlideServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        if "mismatch" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        logger.error(f"Error reordering slides in project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{slug}/slides", response_model=Slide, status_code=status.HTTP_201_CREATED)
async def create_slide(slug: str, request: CreateSlideRequest) -> Slide:
    """Create a new slide in a project.

    Args:
        slug: Project slug identifier
        request: Slide creation request

    Returns:
        Created Slide

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        service = SlideService()
        slide = service.add_slide(slug, request.content)
        return slide

    except SlideServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Error creating slide in project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{slug}/slides/{sid}", response_model=Slide)
async def update_slide(slug: str, sid: str, request: UpdateSlideRequest) -> Slide:
    """Update a slide's content.

    Args:
        slug: Project slug identifier
        sid: Slide identifier
        request: Slide update request with new content

    Returns:
        Updated Slide

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        service = SlideService()
        slide = service.update_slide(slug, sid, request.content)
        return slide

    except SlideServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Error updating slide {sid} in project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{slug}/slides/{sid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slide(slug: str, sid: str) -> None:
    """Delete a slide from a project.

    Args:
        slug: Project slug identifier
        sid: Slide identifier

    Raises:
        HTTPException: 404 if project or slide not found
    """
    try:
        service = SlideService()
        deleted = service.delete_slide(slug, sid)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slide {sid} not found in project {slug}"
            )

    except SlideServiceError as e:
        logger.error(f"Error deleting slide {sid} from project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{slug}/cost", response_model=CostResponse)
async def get_project_cost(slug: str) -> CostResponse:
    """Get the total cost for a project.

    Args:
        slug: Project slug identifier

    Returns:
        CostResponse with total cost

    Raises:
        HTTPException: 404 if project not found
    """
    try:
        service = SlideService()
        project = service.get_project(slug)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {slug} not found"
            )

        return CostResponse(total_cost=project.total_cost)

    except SlideServiceError as e:
        logger.error(f"Error getting cost for project {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
