import React, { useState } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { useUIStore } from '@/stores/uiStore';
import { useDragAndDrop } from '@/hooks/useDragAndDrop';
import { SlideItem } from './SlideItem';
import { SlideInsertLine } from './SlideInsertLine';
import { Button } from '@/components/common/Button';

export function SlideList() {
  const { project, reorderSlides, addSlide } = useSlideStore();
  const { showToast } = useUIStore();
  const [insertPosition, setInsertPosition] = useState<number | null>(null);

  const slides = project?.slides || [];

  const {
    sensors,
    handleDragEnd,
    DndContext,
    SortableContext,
    closestCenter,
    verticalListSortingStrategy,
  } = useDragAndDrop({
    items: slides,
    onReorder: async (newOrder) => {
      try {
        await reorderSlides(newOrder);
      } catch (error) {
        showToast('Failed to reorder slides', 'error');
      }
    },
  });

  const handleInsertClick = (position: number) => {
    setInsertPosition(position);
  };

  const handleInsertConfirm = async (content: string) => {
    if (insertPosition !== null) {
      try {
        await addSlide(content, insertPosition);
        setInsertPosition(null);
        showToast('Slide added successfully', 'success');
      } catch (error) {
        showToast('Failed to add slide', 'error');
      }
    }
  };

  const handleInsertCancel = () => {
    setInsertPosition(null);
  };

  const handleAddSlide = async () => {
    try {
      await addSlide('New slide content');
      showToast('Slide added successfully', 'success');
    } catch (error) {
      showToast('Failed to add slide', 'error');
    }
  };

  if (slides.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-2 text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-[var(--md-soft-blue)] rounded-full flex items-center justify-center">
          <svg
            className="w-8 h-8 text-[var(--md-sky)]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </div>
        <h3 className="text-base font-bold text-[var(--md-ink)] mb-2">
          No Slides Yet
        </h3>
        <p className="text-sm text-[var(--md-slate)] mb-4">
          Add your first slide to get started
        </p>
        <Button
          variant="primary"
          size="sm"
          onClick={handleAddSlide}
        >
          Add Slide
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={slides.map((s) => s.sid)} strategy={verticalListSortingStrategy}>
          {slides.map((slide, index) => (
            <React.Fragment key={slide.sid}>
              {/* Insert line before first slide */}
              {index === 0 && (
                <SlideInsertLine
                  isActive={insertPosition === 0}
                  onClick={() => handleInsertClick(0)}
                  onConfirm={handleInsertConfirm}
                  onCancel={handleInsertCancel}
                />
              )}

              {/* Slide item */}
              <SlideItem slide={slide} index={index} />

              {/* Insert line after each slide */}
              <SlideInsertLine
                isActive={insertPosition === index + 1}
                onClick={() => handleInsertClick(index + 1)}
                onConfirm={handleInsertConfirm}
                onCancel={handleInsertCancel}
              />
            </React.Fragment>
          ))}
        </SortableContext>
      </DndContext>

      {/* Add slide button at bottom */}
      <div className="flex justify-center mt-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleAddSlide}
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          Add Slide
        </Button>
      </div>
    </div>
  );
}
