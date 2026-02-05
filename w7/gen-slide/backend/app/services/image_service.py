"""Image service for image generation operations.

This module provides business logic layer for image generation,
coordinating between the Ark API client and image repository.
"""

import logging
from typing import Tuple, Optional
from app.clients.ark_client import ArkClient, ArkClientError
from app.repositories.image_repository import ImageRepository, ImageRepositoryError
from app.utils.hash import compute_blake3_hash

logger = logging.getLogger(__name__)


class ImageServiceError(Exception):
    """Base exception for image service errors."""
    pass


class ImageService:
    """Service for image generation business logic.

    This class implements image generation workflows, including
    content-based caching and cost tracking.

    Attributes:
        ark_client: Client for Volcano Ark API
        image_repo: Repository for image persistence
    """

    def __init__(
        self,
        ark_client: Optional[ArkClient] = None,
        image_repo: Optional[ImageRepository] = None
    ):
        """Initialize the image service.

        Args:
            ark_client: Ark API client instance
            image_repo: Image repository instance
        """
        self.ark_client = ark_client or ArkClient()
        self.image_repo = image_repo or ImageRepository()

    async def generate_image_for_slide(
        self,
        slug: str,
        sid: str,
        content: str,
        style_prompt: Optional[str] = None,
        style_image: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Tuple[str, float]:
        """Generate an image for a slide with content-based caching.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            content: Slide content to generate image for
            style_prompt: Optional style prompt
            style_image: Optional base64-encoded style reference image
            force_regenerate: If True, regenerate even if cached image exists

        Returns:
            Tuple of (image_hash, cost)

        Raises:
            ImageServiceError: If generation fails
        """
        try:
            # Compute content hash
            content_hash = compute_blake3_hash(content)

            # Check if image already exists (unless force regenerate)
            if not force_regenerate and self.image_repo.image_exists(slug, sid, content_hash):
                logger.info(f"Using cached image for {slug}/{sid}/{content_hash}")
                return content_hash, 0.0

            # Generate prompt combining content and style
            prompt = self._build_prompt(content, style_prompt)

            # Generate image
            if style_image:
                image_bytes, cost = await self.ark_client.generate_image_to_image(
                    prompt=prompt,
                    reference_image=style_image
                )
            else:
                image_bytes, cost = await self.ark_client.generate_text_to_image(
                    prompt=prompt
                )

            # Save image
            self.image_repo.save_image(slug, sid, content_hash, image_bytes)

            logger.info(f"Generated image for {slug}/{sid}/{content_hash}, cost: ${cost:.4f}")
            return content_hash, cost

        except ArkClientError as e:
            logger.error(f"Ark API error: {str(e)}")
            raise ImageServiceError(f"Image generation failed: {str(e)}") from e
        except ImageRepositoryError as e:
            logger.error(f"Image storage error: {str(e)}")
            raise ImageServiceError(f"Failed to save image: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ImageServiceError(f"Unexpected error: {str(e)}") from e

    async def generate_style_reference(
        self,
        prompt: str
    ) -> Tuple[bytes, float]:
        """Generate a style reference image.

        Args:
            prompt: Text description of desired style

        Returns:
            Tuple of (image_bytes, cost)

        Raises:
            ImageServiceError: If generation fails
        """
        try:
            image_bytes, cost = await self.ark_client.generate_text_to_image(
                prompt=prompt
            )

            logger.info(f"Generated style reference, cost: ${cost:.4f}")
            return image_bytes, cost

        except ArkClientError as e:
            logger.error(f"Ark API error: {str(e)}")
            raise ImageServiceError(f"Style generation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ImageServiceError(f"Unexpected error: {str(e)}") from e

    def get_image(
        self,
        slug: str,
        sid: str,
        image_hash: str
    ) -> Optional[bytes]:
        """Retrieve an image by hash.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content

        Returns:
            Image bytes or None if not found

        Raises:
            ImageServiceError: If retrieval fails
        """
        try:
            return self.image_repo.get_image(slug, sid, image_hash)

        except ImageRepositoryError as e:
            logger.error(f"Failed to get image {slug}/{sid}/{image_hash}: {str(e)}")
            raise ImageServiceError(f"Failed to get image: {str(e)}") from e

    def list_images_for_slide(
        self,
        slug: str,
        sid: str
    ) -> list[str]:
        """List all image hashes for a slide.

        Args:
            slug: Project slug identifier
            sid: Slide identifier

        Returns:
            List of image hashes

        Raises:
            ImageServiceError: If listing fails
        """
        try:
            return self.image_repo.list_images(slug, sid)

        except ImageRepositoryError as e:
            logger.error(f"Failed to list images for {slug}/{sid}: {str(e)}")
            raise ImageServiceError(f"Failed to list images: {str(e)}") from e

    def _build_prompt(
        self,
        content: str,
        style_prompt: Optional[str] = None
    ) -> str:
        """Build a complete prompt for image generation.

        Args:
            content: Slide content
            style_prompt: Optional style description

        Returns:
            Combined prompt string
        """
        # Extract key information from content
        # For now, use content directly, but could be enhanced with parsing
        base_prompt = f"Create a professional slide image for: {content}"

        if style_prompt:
            return f"{base_prompt}\n\nStyle: {style_prompt}"

        return base_prompt
