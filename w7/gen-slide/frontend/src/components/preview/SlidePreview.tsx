import { useMemo } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { usePreviewStore } from '@/stores/previewStore';
import { getImageUrl } from '@/services/imageApi';
import { Loading } from '@/components/common/Loading';

export function SlidePreview() {
  const { project, selectedSlideId } = useSlideStore();
  const { currentImageHash, isGenerating } = usePreviewStore();

  // Compute selectedSlide from project and selectedSlideId for proper reactivity
  const selectedSlide = useMemo(() => {
    if (!project || !selectedSlideId) return null;
    return project.slides.find(s => s.sid === selectedSlideId) || null;
  }, [project, selectedSlideId]);

  if (!selectedSlide) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <div className="text-center px-6">
          <div className="w-20 h-20 mx-auto mb-4 bg-[var(--md-soft-blue)] rounded-xl flex items-center justify-center">
            <svg
              className="w-10 h-10 text-[var(--md-sky)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-[var(--md-ink)] mb-2">
            Select a Slide
          </h3>
          <p className="text-[var(--md-slate)] text-sm">
            Choose a slide from the left to preview
          </p>
        </div>
      </div>
    );
  }

  if (isGenerating) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <Loading size="lg" text="Generating image..." />
      </div>
    );
  }

  if (!currentImageHash) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <div className="text-center px-6 max-w-md">
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-[var(--md-soft-blue)] to-[var(--md-fog)] rounded-2xl flex items-center justify-center border-2 border-[var(--md-graphite)]">
            <svg
              className="w-12 h-12 text-[var(--md-sky)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-[var(--md-ink)] mb-2">
            Ready to Generate
          </h3>
          <p className="text-[var(--md-slate)] text-sm mb-4">
            Click "Generate Image" below to create a visual for this slide
          </p>
          <div className="p-4 bg-[var(--md-fog)] rounded-lg border border-[var(--md-graphite)] text-left">
            <p className="text-xs font-bold text-[var(--md-slate)] mb-1 uppercase">
              Content:
            </p>
            <p className="text-sm text-[var(--md-ink)] line-clamp-3">
              {selectedSlide.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="w-full h-full flex items-center justify-center p-4"
      style={{ overflow: 'hidden' }}
    >
      <img
        src={project && selectedSlide ? getImageUrl(project.slug, selectedSlide.sid, currentImageHash) : ''}
        alt={selectedSlide.content}
        className="object-contain rounded-lg border-2 border-[var(--md-graphite)] shadow-[0_4px_0_rgba(0,0,0,1)]"
        style={{ maxWidth: '100%', maxHeight: '100%', width: 'auto', height: 'auto' }}
      />
    </div>
  );
}
