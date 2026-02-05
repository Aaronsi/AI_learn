import { useEffect, useMemo } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { usePreviewStore } from '@/stores/previewStore';
import { computeBlake3Hash } from '@/utils/hash';

/**
 * Custom hook to manage slides and sync with preview
 */
export function useSlides(slug: string) {
  const {
    project,
    selectedSlideId,
    isLoading,
    error,
    loadProject,
    selectSlide,
    updateSlide,
    addSlide,
    deleteSlide,
    reorderSlides,
  } = useSlideStore();

  const { loadImages, clearImages } = usePreviewStore();

  // Load project on mount
  useEffect(() => {
    if (slug) {
      loadProject(slug);
    }
  }, [slug, loadProject]);

  // Get selected slide and its content hash
  const selectedSlide = useMemo(() => {
    return project?.slides.find((slide) => slide.sid === selectedSlideId) || null;
  }, [project?.slides, selectedSlideId]);

  const selectedSlideContentHash = useMemo(() => {
    return selectedSlide ? computeBlake3Hash(selectedSlide.content) : null;
  }, [selectedSlide?.content]);

  // Load images when selected slide changes OR when its content changes
  useEffect(() => {
    if (project && selectedSlideId && selectedSlide) {
      loadImages(project.slug, selectedSlideId, selectedSlideContentHash || undefined);
    } else {
      clearImages();
    }
  }, [project?.slug, selectedSlideId, selectedSlideContentHash, loadImages, clearImages]);

  return {
    project,
    slides: project?.slides || [],
    selectedSlide,
    selectedSlideId,
    isLoading,
    error,
    selectSlide,
    updateSlide,
    addSlide,
    deleteSlide,
    reorderSlides,
  };
}
