"""Image repository for file system operations.

This module provides data access layer for generated images, handling
file storage, retrieval, and listing operations.
"""

import logging
from pathlib import Path
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class ImageRepositoryError(Exception):
    """Base exception for image repository errors."""
    pass


class ImageRepository:
    """Repository for image file persistence.

    This class handles all file system operations for generated images,
    including saving, loading, and listing image files.

    Attributes:
        base_path: Base directory for storing slide projects
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize the image repository.

        Args:
            base_path: Base directory path (defaults to settings.SLIDES_BASE_PATH)
        """
        path_str = base_path or settings.SLIDES_BASE_PATH
        # Resolve relative paths relative to backend directory
        if not Path(path_str).is_absolute():
            # Get backend directory (parent of app directory)
            # __file__ is backend/app/repositories/image_repository.py
            # parent.parent.parent = backend/
            backend_dir = Path(__file__).parent.parent.parent.resolve()
            # Handle ../slides: go up one level from backend/ to w7/gen-slide/, then into slides/
            if path_str.startswith("../"):
                # Remove ../ prefix and resolve relative to backend's parent
                relative_path = path_str[3:]  # Remove "../"
                project_root = backend_dir.parent  # w7/gen-slide/
                self.base_path = (project_root / relative_path).resolve()
            else:
                # Relative path without .., resolve relative to backend/
                self.base_path = (backend_dir / path_str).resolve()
        else:
            self.base_path = Path(path_str).resolve()
        logger.info(f"ImageRepository initialized with base_path: {self.base_path} (absolute: {self.base_path.absolute()})")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_images_path(self, slug: str, sid: str) -> Path:
        """Get the images directory path for a slide.

        Args:
            slug: Project slug identifier
            sid: Slide identifier

        Returns:
            Path to images directory
        """
        return self.base_path / slug / "images" / sid

    def _get_image_path(self, slug: str, sid: str, image_hash: str) -> Path:
        """Get the file path for a specific image.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content

        Returns:
            Path to image file
        """
        return self._get_images_path(slug, sid) / f"{image_hash}.jpg"

    def save_image(
        self,
        slug: str,
        sid: str,
        image_hash: str,
        image_bytes: bytes
    ) -> Path:
        """Save an image to the file system.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content
            image_bytes: Raw image data

        Returns:
            Path to saved image file

        Raises:
            ImageRepositoryError: If saving fails
        """
        try:
            image_path = self._get_image_path(slug, sid, image_hash)
            image_path.parent.mkdir(parents=True, exist_ok=True)

            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            logger.info(f"Saved image: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"Failed to save image {slug}/{sid}/{image_hash}: {str(e)}")
            raise ImageRepositoryError(f"Failed to save image: {str(e)}") from e

    def get_image(
        self,
        slug: str,
        sid: str,
        image_hash: str
    ) -> Optional[bytes]:
        """Retrieve an image from the file system.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content

        Returns:
            Image bytes or None if not found

        Raises:
            ImageRepositoryError: If reading fails
        """
        image_path = self._get_image_path(slug, sid, image_hash)

        if not image_path.exists():
            return None

        try:
            with open(image_path, 'rb') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Failed to read image {slug}/{sid}/{image_hash}: {str(e)}")
            raise ImageRepositoryError(f"Failed to read image: {str(e)}") from e

    def image_exists(
        self,
        slug: str,
        sid: str,
        image_hash: str
    ) -> bool:
        """Check if an image exists.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content

        Returns:
            True if image exists, False otherwise
        """
        image_path = self._get_image_path(slug, sid, image_hash)
        return image_path.exists()

    def list_images(
        self,
        slug: str,
        sid: str
    ) -> List[str]:
        """List all image hashes for a slide.

        Args:
            slug: Project slug identifier
            sid: Slide identifier

        Returns:
            List of image hashes (without .jpg extension)

        Raises:
            ImageRepositoryError: If listing fails
        """
        images_path = self._get_images_path(slug, sid)

        if not images_path.exists():
            return []

        try:
            image_files = list(images_path.glob("*.jpg"))
            return [f.stem for f in image_files]

        except Exception as e:
            logger.error(f"Failed to list images for {slug}/{sid}: {str(e)}")
            raise ImageRepositoryError(f"Failed to list images: {str(e)}") from e

    def delete_image(
        self,
        slug: str,
        sid: str,
        image_hash: str
    ) -> bool:
        """Delete an image from the file system.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            image_hash: Blake3 hash of the image content

        Returns:
            True if deleted, False if not found

        Raises:
            ImageRepositoryError: If deletion fails
        """
        image_path = self._get_image_path(slug, sid, image_hash)

        if not image_path.exists():
            return False

        try:
            image_path.unlink()
            logger.info(f"Deleted image: {image_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete image {slug}/{sid}/{image_hash}: {str(e)}")
            raise ImageRepositoryError(f"Failed to delete image: {str(e)}") from e

    def delete_all_images(
        self,
        slug: str,
        sid: str
    ) -> int:
        """Delete all images for a slide.

        Args:
            slug: Project slug identifier
            sid: Slide identifier

        Returns:
            Number of images deleted

        Raises:
            ImageRepositoryError: If deletion fails
        """
        images_path = self._get_images_path(slug, sid)

        if not images_path.exists():
            return 0

        try:
            import shutil
            image_files = list(images_path.glob("*.jpg"))
            count = len(image_files)

            shutil.rmtree(images_path)
            logger.info(f"Deleted {count} images for {slug}/{sid}")
            return count

        except Exception as e:
            logger.error(f"Failed to delete images for {slug}/{sid}: {str(e)}")
            raise ImageRepositoryError(f"Failed to delete images: {str(e)}") from e

    def _get_style_path(self, slug: str) -> Path:
        """Get the style image file path for a project.

        Args:
            slug: Project slug identifier

        Returns:
            Path to style.jpg file
        """
        return self.base_path / slug / "style.jpg"

    def save_style_image(self, slug: str, image_bytes: bytes) -> Path:
        """Save a style reference image to the file system.

        Args:
            slug: Project slug identifier
            image_bytes: Raw image data

        Returns:
            Path to saved style.jpg file

        Raises:
            ImageRepositoryError: If saving fails
        """
        try:
            style_path = self._get_style_path(slug)
            style_path.parent.mkdir(parents=True, exist_ok=True)

            with open(style_path, 'wb') as f:
                f.write(image_bytes)

            logger.info(f"Saved style image: {style_path}")
            return style_path

        except Exception as e:
            logger.error(f"Failed to save style image for {slug}: {str(e)}")
            raise ImageRepositoryError(f"Failed to save style image: {str(e)}") from e

    def get_style_image(self, slug: str) -> Optional[bytes]:
        """Retrieve the style image from the file system.

        Args:
            slug: Project slug identifier

        Returns:
            Image bytes or None if not found

        Raises:
            ImageRepositoryError: If reading fails
        """
        style_path = self._get_style_path(slug)

        if not style_path.exists():
            return None

        try:
            with open(style_path, 'rb') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Failed to read style image for {slug}: {str(e)}")
            raise ImageRepositoryError(f"Failed to read style image: {str(e)}") from e
