import { useMemo } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { usePreviewStore } from '@/stores/previewStore';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/common/Button';
import { computeBlake3Hash } from '@/utils/hash';

export function GenerateButton() {
  const { project, selectedSlideId, setProject } = useSlideStore();
  const { generateImage, isGenerating, currentImageHash } = usePreviewStore();
  const { showToast } = useUIStore();

  // Compute selectedSlide from project and selectedSlideId for proper reactivity
  const selectedSlide = useMemo(() => {
    if (!project || !selectedSlideId) return null;
    return project.slides.find(s => s.sid === selectedSlideId) || null;
  }, [project, selectedSlideId]);

  if (!selectedSlide || !project) {
    return null;
  }

  // Check if content has changed (hash mismatch)
  const contentHash = computeBlake3Hash(selectedSlide.content);
  const hasContentChanged = contentHash !== currentImageHash;

  // Don't show button if image is up to date
  if (!hasContentChanged && currentImageHash) {
    return null;
  }

  const handleGenerate = async () => {
    if (!project || !selectedSlide) return;

    // Check if style is configured
    if (!project.style) {
      showToast('Please configure a style first', 'error');
      return;
    }

    try {
      await generateImage(project.slug, selectedSlide.sid, selectedSlide.content);

      // Update the slide's has_matching_image status in the store
      const updatedSlides = project.slides.map((slide) =>
        slide.sid === selectedSlide.sid
          ? { ...slide, has_matching_image: true, current_image_hash: contentHash }
          : slide
      );
      setProject({ ...project, slides: updatedSlides });

      showToast('Image generated successfully', 'success');
    } catch (error) {
      showToast('Failed to generate image', 'error');
    }
  };

  return (
    <div className="flex justify-center">
      <Button
        variant="primary"
        size="lg"
        onClick={handleGenerate}
        isLoading={isGenerating}
        disabled={isGenerating}
      >
        <svg
          className="w-5 h-5 mr-2"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
            clipRule="evenodd"
          />
        </svg>
        {isGenerating ? 'Generating...' : 'Generate Image'}
      </Button>
    </div>
  );
}
