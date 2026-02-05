"""Slide service for business logic operations.

This module provides business logic layer for slide management,
coordinating between repositories and implementing domain rules.
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from app.models.slide import SlidesProject, Slide, Style
from app.repositories.slide_repository import SlideRepository, SlideRepositoryError
from app.repositories.image_repository import ImageRepository
from app.utils.hash import compute_blake3_hash

logger = logging.getLogger(__name__)


class SlideServiceError(Exception):
    """Base exception for slide service errors."""
    pass


class SlideService:
    """Service for slide business logic.

    This class implements business rules and coordinates operations
    between repositories for slide management.

    Attributes:
        slide_repo: Repository for slide persistence
        image_repo: Repository for image persistence
    """

    def __init__(
        self,
        slide_repo: Optional[SlideRepository] = None,
        image_repo: Optional[ImageRepository] = None
    ):
        """Initialize the slide service.

        Args:
            slide_repo: Slide repository instance
            image_repo: Image repository instance
        """
        self.slide_repo = slide_repo or SlideRepository()
        self.image_repo = image_repo or ImageRepository()

    def get_project(self, slug: str) -> Optional[SlidesProject]:
        """Retrieve a project with computed image metadata.

        Args:
            slug: Project slug identifier

        Returns:
            SlidesProject with current_image_hash and has_matching_image computed

        Raises:
            SlideServiceError: If retrieval fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                return None

            # Compute dynamic fields for each slide
            for slide in project.slides:
                self._compute_slide_image_metadata(project.slug, slide)

            return project

        except SlideRepositoryError as e:
            logger.error(f"Failed to get project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to get project: {str(e)}") from e

    def create_project(self, slug: str, title: str) -> SlidesProject:
        """Create a new slide project.

        Args:
            slug: URL-safe project identifier
            title: Human-readable project title

        Returns:
            Created SlidesProject instance

        Raises:
            SlideServiceError: If creation fails or project exists
        """
        try:
            if self.slide_repo.exists(slug):
                raise SlideServiceError(f"Project {slug} already exists")

            project = SlidesProject(
                slug=slug,
                title=title,
                style=None,
                slides=[],
                total_cost=0.0
            )

            return self.slide_repo.create(project)

        except SlideRepositoryError as e:
            logger.error(f"Failed to create project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to create project: {str(e)}") from e

    def update_project_title(self, slug: str, title: str) -> SlidesProject:
        """Update a project's title.

        Args:
            slug: Project slug identifier
            title: New project title

        Returns:
            Updated SlidesProject instance

        Raises:
            SlideServiceError: If project not found or update fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            project.title = title
            return self.slide_repo.update(project)

        except SlideRepositoryError as e:
            logger.error(f"Failed to update project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to update project: {str(e)}") from e

    def add_slide(self, slug: str, content: str) -> Slide:
        """Add a new slide to a project.

        Args:
            slug: Project slug identifier
            content: Markdown content for the slide

        Returns:
            Created Slide instance

        Raises:
            SlideServiceError: If project not found or addition fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            now = datetime.now()
            slide = Slide(
                sid=str(uuid4()),
                content=content,
                created_at=now,
                updated_at=now
            )

            project.slides.append(slide)
            self.slide_repo.update(project)

            # Compute image metadata
            self._compute_slide_image_metadata(slug, slide)

            logger.info(f"Added slide {slide.sid} to project {slug}")
            return slide

        except SlideRepositoryError as e:
            logger.error(f"Failed to add slide to project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to add slide: {str(e)}") from e

    def update_slide(self, slug: str, sid: str, content: str) -> Slide:
        """Update a slide's content.

        Args:
            slug: Project slug identifier
            sid: Slide identifier
            content: New markdown content

        Returns:
            Updated Slide instance

        Raises:
            SlideServiceError: If project or slide not found or update fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            slide = self._find_slide(project, sid)
            if not slide:
                raise SlideServiceError(f"Slide {sid} not found")

            slide.content = content
            slide.updated_at = datetime.now()

            self.slide_repo.update(project)

            # Compute image metadata
            self._compute_slide_image_metadata(slug, slide)

            logger.info(f"Updated slide {sid} in project {slug}")
            return slide

        except SlideRepositoryError as e:
            logger.error(f"Failed to update slide {sid} in project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to update slide: {str(e)}") from e

    def delete_slide(self, slug: str, sid: str) -> bool:
        """Delete a slide from a project.

        Args:
            slug: Project slug identifier
            sid: Slide identifier

        Returns:
            True if deleted, False if not found

        Raises:
            SlideServiceError: If deletion fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                return False

            original_count = len(project.slides)
            project.slides = [s for s in project.slides if s.sid != sid]

            if len(project.slides) == original_count:
                return False

            self.slide_repo.update(project)

            # Delete associated images
            try:
                self.image_repo.delete_all_images(slug, sid)
            except Exception as e:
                logger.warning(f"Failed to delete images for slide {sid}: {str(e)}")

            logger.info(f"Deleted slide {sid} from project {slug}")
            return True

        except SlideRepositoryError as e:
            logger.error(f"Failed to delete slide {sid} from project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to delete slide: {str(e)}") from e

    def reorder_slides(self, slug: str, slide_ids: List[str]) -> SlidesProject:
        """Reorder slides in a project.

        Args:
            slug: Project slug identifier
            slide_ids: Ordered list of slide IDs

        Returns:
            Updated SlidesProject instance

        Raises:
            SlideServiceError: If project not found or reordering fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            # Validate all slide IDs exist
            existing_ids = {s.sid for s in project.slides}
            provided_ids = set(slide_ids)

            if existing_ids != provided_ids:
                raise SlideServiceError("Slide IDs mismatch")

            # Create lookup map
            slide_map = {s.sid: s for s in project.slides}

            # Reorder slides
            project.slides = [slide_map[sid] for sid in slide_ids]

            self.slide_repo.update(project)

            logger.info(f"Reordered slides in project {slug}")
            return project

        except SlideRepositoryError as e:
            logger.error(f"Failed to reorder slides in project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to reorder slides: {str(e)}") from e

    def update_style(self, slug: str, style: Style) -> SlidesProject:
        """Update the style for a project.

        Args:
            slug: Project slug identifier
            style: Style configuration

        Returns:
            Updated SlidesProject instance

        Raises:
            SlideServiceError: If project not found or update fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            project.style = style
            return self.slide_repo.update(project)

        except SlideRepositoryError as e:
            logger.error(f"Failed to update style for project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to update style: {str(e)}") from e

    def update_total_cost(self, slug: str, additional_cost: float) -> float:
        """Update the total cost for a project.

        Args:
            slug: Project slug identifier
            additional_cost: Cost to add to total

        Returns:
            Updated total cost

        Raises:
            SlideServiceError: If project not found or update fails
        """
        try:
            project = self.slide_repo.get(slug)
            if not project:
                raise SlideServiceError(f"Project {slug} not found")

            project.total_cost += additional_cost
            self.slide_repo.update(project)

            logger.info(f"Updated total cost for project {slug}: ${project.total_cost:.4f}")
            return project.total_cost

        except SlideRepositoryError as e:
            logger.error(f"Failed to update cost for project {slug}: {str(e)}")
            raise SlideServiceError(f"Failed to update cost: {str(e)}") from e

    def _find_slide(self, project: SlidesProject, sid: str) -> Optional[Slide]:
        """Find a slide by ID within a project.

        Args:
            project: SlidesProject instance
            sid: Slide identifier

        Returns:
            Slide instance or None if not found
        """
        for slide in project.slides:
            if slide.sid == sid:
                return slide
        return None

    def _compute_slide_image_metadata(self, slug: str, slide: Slide) -> None:
        """Compute and set image metadata for a slide.

        Args:
            slug: Project slug identifier
            slide: Slide instance to update
        """
        # Compute hash of current content
        slide.current_image_hash = compute_blake3_hash(slide.content)

        # Check if matching image exists
        slide.has_matching_image = self.image_repo.image_exists(
            slug,
            slide.sid,
            slide.current_image_hash
        )
