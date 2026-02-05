import { useState, useEffect, useRef } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { usePreviewStore } from '@/stores/previewStore';
import { useUIStore } from '@/stores/uiStore';
import type { Slide } from '@/types/slide';
import { Button } from '@/components/common/Button';
import { computeBlake3Hash } from '@/utils/hash';

interface SlideEditorProps {
  slide: Slide;
  onComplete: () => void;
}

export function SlideEditor({ slide, onComplete }: SlideEditorProps) {
  const { project, updateSlide } = useSlideStore();
  const { generateImage } = usePreviewStore();
  const { showToast } = useUIStore();
  const [content, setContent] = useState(slide.content);
  const [isSaving, setIsSaving] = useState(false);
  const [statusText, setStatusText] = useState('Save');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Focus and select all text when editor opens
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, []);

  const handleSave = async () => {
    if (content.trim() === '') {
      showToast('Slide content cannot be empty', 'error');
      return;
    }

    if (content === slide.content) {
      onComplete();
      return;
    }

    if (!project) {
      showToast('Project not found', 'error');
      return;
    }

    setIsSaving(true);
    setStatusText('Saving...');

    try {
      // First update the slide content
      await updateSlide(slide.sid, content);

      // Auto-generate image if style is configured
      if (project.style) {
        setStatusText('Generating image...');
        try {
          await generateImage(project.slug, slide.sid, content);

          // Update has_matching_image in the store
          const contentHash = computeBlake3Hash(content);
          const currentProject = useSlideStore.getState().project;
          if (currentProject) {
            const updatedSlides = currentProject.slides.map((s) =>
              s.sid === slide.sid
                ? { ...s, has_matching_image: true, current_image_hash: contentHash }
                : s
            );
            useSlideStore.getState().setProject({ ...currentProject, slides: updatedSlides });
          }

          showToast('Image generated successfully', 'success');
        } catch (error) {
          console.error('Failed to generate image:', error);
          showToast('Failed to generate image', 'error');
        }
      } else {
        showToast('Slide saved. Configure a style to generate images.', 'info');
      }

      onComplete();
    } catch (error) {
      console.error('Failed to update slide:', error);
      showToast('Failed to update slide', 'error');
      setStatusText('Save');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setContent(slide.content);
    onComplete();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSave();
    }
  };

  return (
    <div className="p-3 rounded-lg border-2 border-[var(--md-sky)] bg-[var(--md-cloud)] shadow-lg">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full min-h-[120px] p-2 border-2 border-[var(--md-graphite)] rounded bg-[var(--md-fog)] text-[var(--md-ink)] text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--md-sky)]"
        placeholder="Enter slide content..."
        disabled={isSaving}
      />
      <div className="flex items-center justify-end gap-2 mt-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={handleSave}
          isLoading={isSaving}
        >
          {statusText}
        </Button>
      </div>
      <p className="text-xs text-[var(--md-slate)] mt-2">
        Press Ctrl+Enter to save, Esc to cancel
      </p>
    </div>
  );
}
