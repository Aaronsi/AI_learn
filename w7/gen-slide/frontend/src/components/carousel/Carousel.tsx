import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useSlideStore } from '@/stores/slideStore';
import { useUIStore } from '@/stores/uiStore';
import { useCarousel } from '@/hooks/useCarousel';
import { getImageUrl } from '@/services/imageApi';

export function Carousel() {
  const { project, selectedSlideId } = useSlideStore();
  const { isCarouselOpen, closeCarousel } = useUIStore();

  const slides = project?.slides || [];

  const {
    currentIndex,
    currentSlide,
    hasNext,
    hasPrevious,
    goToNext,
    goToPrevious,
  } = useCarousel({
    slides,
    initialSlideId: selectedSlideId,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isCarouselOpen) return;

      if (e.key === 'Escape') {
        closeCarousel();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCarouselOpen, closeCarousel]);

  if (!isCarouselOpen || !currentSlide) {
    return null;
  }

  const carouselContent = (
    <div className="fixed inset-0 z-[9999] bg-black">
      {/* Close button */}
      <button
        onClick={closeCarousel}
        className="absolute top-4 right-4 z-10 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
        aria-label="Close carousel"
      >
        <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Slide counter */}
      <div className="absolute top-4 left-4 z-10 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full">
        <span className="text-white font-medium">
          {currentIndex + 1} / {slides.length}
        </span>
      </div>

      {/* Main content */}
      <div className="w-full h-full flex items-center justify-center p-8">
        {currentSlide.current_image_hash && project ? (
          <div className="relative max-w-6xl w-full">
            <img
              src={getImageUrl(project.slug, currentSlide.sid, currentSlide.current_image_hash)}
              alt={currentSlide.content}
              className="w-full h-auto max-h-[80vh] object-contain"
            />
            {/* Content overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-8">
              <p className="text-white text-lg">{currentSlide.content}</p>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <svg
              className="w-32 h-32 mx-auto text-white/30 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-white text-xl mb-2">No image for this slide</p>
            <p className="text-white/70">{currentSlide.content}</p>
          </div>
        )}
      </div>

      {/* Navigation buttons */}
      {hasPrevious && (
        <button
          onClick={goToPrevious}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-4 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          aria-label="Previous slide"
        >
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}

      {hasNext && (
        <button
          onClick={goToNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-4 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
          aria-label="Next slide"
        >
          <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}

      {/* Keyboard hints */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-4 text-white/70 text-sm">
        <span>← → Navigate</span>
        <span>ESC Close</span>
      </div>
    </div>
  );

  // Use portal to render carousel at document body level
  return createPortal(carouselContent, document.body);
}
