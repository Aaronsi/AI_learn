import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';

export interface UseDragAndDropProps {
  items: Array<{ sid: string }>;
  onReorder: (newOrder: string[]) => void;
}

/**
 * Custom hook for drag and drop functionality
 */
export function useDragAndDrop({ items, onReorder }: UseDragAndDropProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex((item) => item.sid === active.id);
      const newIndex = items.findIndex((item) => item.sid === over.id);

      const newItems = arrayMove(items, oldIndex, newIndex);
      const newOrder = newItems.map((item) => item.sid);
      onReorder(newOrder);
    }
  };

  return {
    sensors,
    handleDragEnd,
    DndContext,
    SortableContext,
    closestCenter,
    verticalListSortingStrategy,
  };
}
