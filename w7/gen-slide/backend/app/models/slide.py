"""Data models for slides and styles.

This module defines the core domain models for the GenSlides application,
including slides, styles, and project structures.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Style(BaseModel):
    """Style configuration for slide image generation.

    Attributes:
        prompt: Text prompt describing the desired visual style
        image: Style image file path (e.g., "style.jpg") or base64-encoded image data
    """

    prompt: str = Field(..., description="Style description prompt")
    image: str = Field(..., description="Style image file path or base64-encoded image")


class Slide(BaseModel):
    """Individual slide within a presentation project.

    Attributes:
        sid: Unique slide identifier
        content: Markdown content of the slide
        created_at: Timestamp when slide was created
        updated_at: Timestamp when slide was last modified
        current_image_hash: Blake3 hash of current content (computed dynamically)
        has_matching_image: Whether an image exists for current content hash
    """

    sid: str = Field(..., description="Unique slide identifier")
    content: str = Field(..., description="Slide markdown content")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    current_image_hash: str = Field(
        default="",
        description="Blake3 hash of current content"
    )
    has_matching_image: bool = Field(
        default=False,
        description="Whether matching image exists"
    )


class SlidesProject(BaseModel):
    """Complete slide presentation project.

    Attributes:
        slug: URL-safe project identifier
        title: Human-readable project title
        style: Optional style configuration for image generation
        slides: List of slides in the project
        total_cost: Cumulative cost of all image generations
    """

    slug: str = Field(..., description="URL-safe project identifier")
    title: str = Field(..., description="Project title")
    style: Optional[Style] = Field(None, description="Style configuration")
    slides: list[Slide] = Field(default_factory=list, description="Project slides")
    total_cost: float = Field(default=0.0, description="Total generation cost")
