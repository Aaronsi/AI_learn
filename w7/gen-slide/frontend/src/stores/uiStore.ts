import { create } from 'zustand';

interface Toast {
  message: string;
  type: 'success' | 'error' | 'info';
}

interface UIStore {
  isStyleSelectorOpen: boolean;
  isCarouselOpen: boolean;
  toast: Toast | null;

  // Actions
  openStyleSelector: () => void;
  closeStyleSelector: () => void;
  openCarousel: () => void;
  closeCarousel: () => void;
  showToast: (message: string, type: Toast['type']) => void;
  hideToast: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isStyleSelectorOpen: false,
  isCarouselOpen: false,
  toast: null,

  openStyleSelector: () => set({ isStyleSelectorOpen: true }),
  closeStyleSelector: () => set({ isStyleSelectorOpen: false }),
  openCarousel: () => set({ isCarouselOpen: true }),
  closeCarousel: () => set({ isCarouselOpen: false }),

  showToast: (message: string, type: Toast['type']) => {
    set({ toast: { message, type } });
    // Auto-hide toast after 3 seconds
    setTimeout(() => {
      set({ toast: null });
    }, 3000);
  },

  hideToast: () => set({ toast: null }),
}));
