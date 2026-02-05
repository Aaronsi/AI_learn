"""Style service for style management operations.

This module provides business logic layer for style generation and selection,
coordinating between image generation and project updates.
"""

import logging
import base64
from typing import Tuple
from app.models.slide import Style
from app.services.image_service import ImageService, ImageServiceError
from app.repositories.image_repository import ImageRepository, ImageRepositoryError

logger = logging.getLogger(__name__)


class StyleServiceError(Exception):
    """Base exception for style service errors."""
    pass


class StyleService:
    """Service for style management business logic.

    This class implements style generation and selection workflows.

    Attributes:
        image_service: Service for image generation
    """

    def __init__(self, image_service: ImageService = None, image_repo: ImageRepository = None):
        """Initialize the style service.

        Args:
            image_service: Image service instance
            image_repo: Image repository instance
        """
        self.image_service = image_service or ImageService()
        self.image_repo = image_repo or ImageRepository()

    async def generate_style(self, prompt: str) -> Tuple[str, float]:
        """Generate a style reference image.

        Args:
            prompt: Text description of desired style

        Returns:
            Tuple of (base64_encoded_image, cost)

        Raises:
            StyleServiceError: If generation fails
        """
        try:
            image_bytes, cost = await self.image_service.generate_style_reference(prompt)

            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            logger.info(f"Generated style reference, cost: ${cost:.4f}")
            return base64_image, cost

        except ImageServiceError as e:
            logger.error(f"Failed to generate style: {str(e)}")
            raise StyleServiceError(f"Failed to generate style: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise StyleServiceError(f"Unexpected error: {str(e)}") from e

    def create_style(self, prompt: str, base64_image: str) -> Style:
        """Create a Style object from prompt and image.

        Args:
            prompt: Style description prompt
            base64_image: Base64-encoded reference image

        Returns:
            Style instance

        Raises:
            StyleServiceError: If validation fails
        """
        try:
            # Validate base64 image
            if not base64_image:
                raise StyleServiceError("Image data is required")

            # Remove data URL prefix if present
            if base64_image.startswith('data:image/'):
                base64_image = base64_image.split(',', 1)[1]

            # Validate base64 encoding
            try:
                base64.b64decode(base64_image)
            except Exception as e:
                raise StyleServiceError(f"Invalid base64 image data: {str(e)}")

            style = Style(prompt=prompt, image=base64_image)

            logger.info("Created style configuration")
            return style

        except Exception as e:
            if isinstance(e, StyleServiceError):
                raise
            logger.error(f"Failed to create style: {str(e)}")
            raise StyleServiceError(f"Failed to create style: {str(e)}") from e

    def save_style_image(self, slug: str, base64_image: str) -> Style:
        """Save style image to file system and create Style object.

        Args:
            slug: Project slug identifier
            base64_image: Base64-encoded reference image

        Returns:
            Style instance with image field set to "style.jpg"

        Raises:
            StyleServiceError: If validation or saving fails
        """
        try:
            # Validate and decode base64 image
            if not base64_image:
                raise StyleServiceError("Image data is required")

            # Remove data URL prefix if present
            if base64_image.startswith('data:image/'):
                base64_image = base64_image.split(',', 1)[1]

            # Decode base64 to bytes
            try:
                image_bytes = base64.b64decode(base64_image)
            except Exception as e:
                raise StyleServiceError(f"Invalid base64 image data: {str(e)}")

            # Save image to file system
            try:
                self.image_repo.save_style_image(slug, image_bytes)
            except ImageRepositoryError as e:
                raise StyleServiceError(f"Failed to save style image: {str(e)}") from e

            # Create Style object with file path
            style = Style(prompt="", image="style.jpg")  # prompt will be set by caller

            logger.info(f"Saved style image for project {slug}")
            return style

        except Exception as e:
            if isinstance(e, StyleServiceError):
                raise
            logger.error(f"Failed to save style image: {str(e)}")
            raise StyleServiceError(f"Failed to save style image: {str(e)}") from e
