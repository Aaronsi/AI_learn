"""API request and response schemas.

This module defines Pydantic models for API request validation and
response serialization, separate from domain models.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CreateProjectRequest(BaseModel):
    """Request to create a new slide project.

    Attributes:
        slug: URL-safe project identifier
        title: Human-readable project title
    """

    slug: str = Field(..., min_length=1, description="URL-safe project identifier")
    title: str = Field(..., min_length=1, description="Project title")


class UpdateProjectRequest(BaseModel):
    """Request to update project metadata.

    Attributes:
        title: Updated project title
    """

    title: str = Field(..., min_length=1, description="Updated project title")


class ReorderSlidesRequest(BaseModel):
    """Request to reorder slides in a project.

    Attributes:
        slide_ids: Ordered list of slide IDs
    """

    slide_ids: list[str] = Field(..., description="Ordered list of slide IDs")


class CreateSlideRequest(BaseModel):
    """Request to create a new slide.

    Attributes:
        content: Markdown content for the slide
    """

    content: str = Field(..., description="Slide markdown content")


class UpdateSlideRequest(BaseModel):
    """Request to update a slide's content.

    Attributes:
        content: Updated markdown content for the slide
    """

    content: Optional[str] = Field(None, description="Updated slide markdown content")


class GenerateStyleRequest(BaseModel):
    """Request to generate a style reference image.

    Attributes:
        prompt: Text description of desired style
    """

    prompt: str = Field(..., min_length=1, description="Style description prompt")


class SelectStyleRequest(BaseModel):
    """Request to select a style for the project.

    Attributes:
        prompt: Style description prompt
        image: Base64-encoded reference image
    """

    prompt: str = Field(..., description="Style description prompt")
    image: str = Field(..., description="Base64-encoded reference image")


class GenerateImageResponse(BaseModel):
    """Response from image generation endpoint.

    Attributes:
        image_hash: Blake3 hash identifying the generated image
        cost: Cost of the generation operation
        message: Optional status message
    """

    image_hash: str = Field(..., description="Generated image hash")
    cost: float = Field(..., description="Generation cost")
    message: Optional[str] = Field(None, description="Status message")


class CostResponse(BaseModel):
    """Response containing total project cost.

    Attributes:
        total_cost: Cumulative cost of all generations
    """

    total_cost: float = Field(..., description="Total project cost")


class ErrorResponse(BaseModel):
    """Standard error response format.

    Attributes:
        detail: Error message or description
    """

    detail: str = Field(..., description="Error message")
