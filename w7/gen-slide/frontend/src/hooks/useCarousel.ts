import { useState, useEffect, useCallback } from 'react';
import type { Slide } from '@/types/slide';

export interface UseCarouselProps {
  slides: Slide[];
  initialSlideId?: string | null;
}

/**
 * Custom hook for carousel navigation
 */
export function useCarousel({ slides, initialSlideId }: UseCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Set initial index based on initialSlideId
  useEffect(() => {
    if (initialSlideId) {
      const index = slides.findIndex((slide) => slide.sid === initialSlideId);
      if (index !== -1) {
        setCurrentIndex(index);
      }
    }
  }, [initialSlideId, slides]);

  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % slides.length);
  }, [slides.length]);

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + slides.length) % slides.length);
  }, [slides.length]);

  const goToSlide = useCallback((index: number) => {
    setCurrentIndex(index);
  }, []);

  const currentSlide = slides[currentIndex];
  const hasNext = currentIndex < slides.length - 1;
  const hasPrevious = currentIndex > 0;

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && hasNext) {
        goToNext();
      } else if (e.key === 'ArrowLeft' && hasPrevious) {
        goToPrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasNext, hasPrevious, goToNext, goToPrevious]);

  return {
    currentIndex,
    currentSlide,
    hasNext,
    hasPrevious,
    goToNext,
    goToPrevious,
    goToSlide,
  };
}
