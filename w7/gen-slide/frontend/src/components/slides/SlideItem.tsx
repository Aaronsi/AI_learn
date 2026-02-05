import { useState } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useSlideStore } from '@/stores/slideStore';
import { useUIStore } from '@/stores/uiStore';
import type { Slide } from '@/types/slide';
import { SlideEditor } from './SlideEditor';
import { truncateText } from '@/utils/helpers';
import { getImageUrl } from '@/services/imageApi';
import { computeBlake3Hash } from '@/utils/hash';

interface SlideItemProps {
  slide: Slide;
  index: number;
}

export function SlideItem({ slide, index }: SlideItemProps) {
  const { project, selectedSlideId, selectSlide, deleteSlide } = useSlideStore();
  const { showToast } = useUIStore();
  const [isEditing, setIsEditing] = useState(false);
  const [imageError, setImageError] = useState(false);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: slide.sid });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const isSelected = selectedSlideId === slide.sid;

  // Calculate content hash to get the matching image
  const contentHash = computeBlake3Hash(slide.content);
  const hasImage = slide.has_matching_image && project;
  const imageUrl = hasImage ? getImageUrl(project.slug, slide.sid, contentHash) : null;

  const handleClick = () => {
    if (!isEditing) {
      selectSlide(slide.sid);
    }
  };

  const handleDoubleClick = () => {
    setIsEditing(true);
  };

  const handleEditComplete = () => {
    setIsEditing(false);
    setImageError(false);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this slide?')) {
      try {
        await deleteSlide(slide.sid);
        showToast('Slide deleted successfully', 'success');
      } catch (error) {
        showToast('Failed to delete slide', 'error');
      }
    }
  };

  const handleImageError = () => {
    setImageError(true);
  };

  if (isEditing) {
    return (
      <div ref={setNodeRef} style={style}>
        <SlideEditor slide={slide} onComplete={handleEditComplete} />
      </div>
    );
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      className={`group relative cursor-pointer transition-all overflow-hidden rounded ${
        isSelected
          ? 'ring-2 ring-[var(--md-sky)] shadow-md'
          : 'hover:ring-1 hover:ring-[var(--md-sky)] hover:shadow-sm'
      }`}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >

      {/* Delete button - appears on hover */}
      <button
        onClick={handleDelete}
        className="absolute right-1 top-1 z-10 p-0.5 rounded bg-black/30 hover:bg-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label="Delete slide"
      >
        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Thumbnail - also serves as drag handle */}
      {imageUrl && !imageError ? (
        <div
          {...listeners}
          className="aspect-video w-full bg-[var(--md-fog)] cursor-grab active:cursor-grabbing"
        >
          <img
            src={imageUrl}
            alt={`Slide ${index + 1}`}
            className="w-full h-full object-cover pointer-events-none"
            onError={handleImageError}
          />
        </div>
      ) : (
        <div
          {...listeners}
          className="aspect-video w-full bg-[var(--md-fog)] flex items-center justify-center cursor-grab active:cursor-grabbing"
        >
          <svg
            className="w-10 h-10 text-[var(--md-slate)] pointer-events-none"
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
        </div>
      )}

      {/* Content text */}
      <div className="p-2 bg-[var(--md-cloud)]">
        <p className="text-xs text-[var(--md-ink)] line-clamp-2">
          {truncateText(slide.content, 50)}
        </p>
      </div>
    </div>
  );
}
