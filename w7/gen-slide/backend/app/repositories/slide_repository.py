"""Slide repository for data persistence operations.

This module provides data access layer for slide projects, handling YAML file
operations and directory management.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from app.models.slide import SlidesProject, Slide, Style
from app.utils.yaml_handler import read_yaml, write_yaml
from app.config import settings

logger = logging.getLogger(__name__)


class SlideRepositoryError(Exception):
    """Base exception for slide repository errors."""
    pass


class SlideRepository:
    """Repository for slide project persistence.

    This class handles all file system operations for slide projects,
    including reading and writing outline.yml files.

    Attributes:
        base_path: Base directory for storing slide projects
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize the slide repository.

        Args:
            base_path: Base directory path (defaults to settings.SLIDES_BASE_PATH)
        """
        path_str = base_path or settings.SLIDES_BASE_PATH
        # Resolve relative paths relative to backend directory
        if not Path(path_str).is_absolute():
            # Get backend directory (parent of app directory)
            # __file__ is backend/app/repositories/slide_repository.py
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
        logger.info(f"SlideRepository initialized with base_path: {self.base_path} (absolute: {self.base_path.absolute()})")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_project_path(self, slug: str) -> Path:
        """Get the directory path for a project.

        Args:
            slug: Project slug identifier

        Returns:
            Path to project directory
        """
        return self.base_path / slug

    def _get_outline_path(self, slug: str) -> Path:
        """Get the outline.yml file path for a project.

        Args:
            slug: Project slug identifier

        Returns:
            Path to outline.yml file
        """
        return self._get_project_path(slug) / "outline.yml"

    def exists(self, slug: str) -> bool:
        """Check if a project exists.

        Args:
            slug: Project slug identifier

        Returns:
            True if project exists, False otherwise
        """
        outline_path = self._get_outline_path(slug)
        exists = outline_path.exists()
        logger.info(f"Checking if project {slug} exists at {outline_path} (absolute: {outline_path.absolute()}): {exists}")
        return exists

    def get(self, slug: str) -> Optional[SlidesProject]:
        """Retrieve a slide project by slug.

        Args:
            slug: Project slug identifier

        Returns:
            SlidesProject instance or None if not found

        Raises:
            SlideRepositoryError: If file reading fails
        """
        outline_path = self._get_outline_path(slug)
        logger.info(f"Loading project {slug} from {outline_path} (absolute: {outline_path.absolute()})")

        if not outline_path.exists():
            logger.info(f"Project {slug} not found at {outline_path}")
            return None

        try:
            data = read_yaml(outline_path)
            # Handle empty YAML file (yaml.safe_load returns None for empty files)
            if data is None:
                return None
            return self._deserialize_project(data)
        except Exception as e:
            logger.error(f"Failed to read project {slug}: {str(e)}")
            raise SlideRepositoryError(f"Failed to read project: {str(e)}") from e

    def create(self, project: SlidesProject) -> SlidesProject:
        """Create a new slide project.

        Args:
            project: SlidesProject instance to create

        Returns:
            Created SlidesProject instance

        Raises:
            SlideRepositoryError: If project already exists or creation fails
        """
        outline_path = self._get_outline_path(project.slug)
        logger.info(f"Creating project {project.slug} at {outline_path} (absolute: {outline_path.absolute()})")
        
        if self.exists(project.slug):
            logger.warning(f"Project {project.slug} already exists at {outline_path}")
            raise SlideRepositoryError(f"Project {project.slug} already exists")

        try:
            # Create project directory
            project_path = self._get_project_path(project.slug)
            project_path.mkdir(parents=True, exist_ok=True)

            # Write outline.yml
            self._write_project(project)

            logger.info(f"Created project: {project.slug}")
            return project

        except Exception as e:
            logger.error(f"Failed to create project {project.slug}: {str(e)}")
            raise SlideRepositoryError(f"Failed to create project: {str(e)}") from e

    def update(self, project: SlidesProject) -> SlidesProject:
        """Update an existing slide project.

        Args:
            project: SlidesProject instance with updated data

        Returns:
            Updated SlidesProject instance

        Raises:
            SlideRepositoryError: If project doesn't exist or update fails
        """
        if not self.exists(project.slug):
            raise SlideRepositoryError(f"Project {project.slug} not found")

        try:
            self._write_project(project)
            logger.info(f"Updated project: {project.slug}")
            return project

        except Exception as e:
            logger.error(f"Failed to update project {project.slug}: {str(e)}")
            raise SlideRepositoryError(f"Failed to update project: {str(e)}") from e

    def delete(self, slug: str) -> bool:
        """Delete a slide project.

        Args:
            slug: Project slug identifier

        Returns:
            True if deleted, False if not found

        Raises:
            SlideRepositoryError: If deletion fails
        """
        project_path = self._get_project_path(slug)

        if not project_path.exists():
            return False

        try:
            import shutil
            shutil.rmtree(project_path)
            logger.info(f"Deleted project: {slug}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete project {slug}: {str(e)}")
            raise SlideRepositoryError(f"Failed to delete project: {str(e)}") from e

    def _write_project(self, project: SlidesProject) -> None:
        """Write project data to outline.yml.

        Args:
            project: SlidesProject instance to write

        Raises:
            SlideRepositoryError: If writing fails
        """
        outline_path = self._get_outline_path(project.slug)
        data = self._serialize_project(project)

        try:
            write_yaml(outline_path, data)
        except Exception as e:
            raise SlideRepositoryError(f"Failed to write project: {str(e)}") from e

    def _serialize_project(self, project: SlidesProject) -> dict:
        """Serialize a SlidesProject to dictionary format.

        Args:
            project: SlidesProject instance

        Returns:
            Dictionary representation for YAML serialization
        """
        data = {
            "slug": project.slug,
            "title": project.title,
            "slides": [
                {
                    "sid": slide.sid,
                    "content": slide.content,
                    "created_at": slide.created_at,
                    "updated_at": slide.updated_at,
                }
                for slide in project.slides
            ],
            "total_cost": project.total_cost,
        }

        if project.style:
            data["style"] = {
                "prompt": project.style.prompt,
                "image": project.style.image,
            }

        return data

    def _deserialize_project(self, data: dict) -> SlidesProject:
        """Deserialize a dictionary to SlidesProject.

        Args:
            data: Dictionary from YAML file

        Returns:
            SlidesProject instance
        """
        slides = [
            Slide(
                sid=slide_data["sid"],
                content=slide_data["content"],
                created_at=slide_data["created_at"],
                updated_at=slide_data["updated_at"],
            )
            for slide_data in data.get("slides", [])
        ]

        style = None
        if "style" in data and data["style"]:
            style = Style(
                prompt=data["style"]["prompt"],
                image=data["style"]["image"],
            )

        return SlidesProject(
            slug=data["slug"],
            title=data["title"],
            style=style,
            slides=slides,
            total_cost=data.get("total_cost", 0.0),
        )
