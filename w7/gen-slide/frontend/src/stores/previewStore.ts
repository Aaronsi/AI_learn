import { create } from 'zustand';
import * as imageApi from '@/services/imageApi';

interface ImageInfo {
  hash: string;
  url: string;
  content?: string; // The slide content when this image was generated
}

interface PreviewStore {
  currentImageHash: string | null;
  images: ImageInfo[];
  isGenerating: boolean;
  error: string | null;

  // Actions
  loadImages: (slug: string, slideId: string, currentContentHash?: string) => Promise<void>;
  generateImage: (slug: string, slideId: string, content: string) => Promise<void>;
  setCurrentImageHash: (hash: string | null) => void;
  clearImages: () => void;
}

export const usePreviewStore = create<PreviewStore>((set) => ({
  currentImageHash: null,
  images: [],
  isGenerating: false,
  error: null,

  loadImages: async (slug: string, slideId: string, currentContentHash?: string) => {
    try {
      const hashes = await imageApi.getSlideImages(slug, slideId);

      // Convert hash list to ImageInfo array
      const images: ImageInfo[] = hashes.map((hash) => ({
        hash,
        url: imageApi.getImageUrl(slug, slideId, hash),
      }));

      // Determine current image: prefer matching content hash, otherwise use first (most recent)
      let currentHash: string | null = null;
      if (currentContentHash && hashes.includes(currentContentHash)) {
        currentHash = currentContentHash;
      } else if (hashes.length > 0) {
        currentHash = hashes[0];
      }

      set({
        images,
        currentImageHash: currentHash,
        error: null,
      });
    } catch (error: any) {
      // If 404 or empty, just clear images without error
      set({ images: [], currentImageHash: null, error: null });
    }
  },

  generateImage: async (slug: string, slideId: string, content: string) => {
    set({ isGenerating: true, error: null });
    try {
      const result = await imageApi.generateImage(slug, slideId);

      // Add new image to the list with the content that was used to generate it
      const newImage: ImageInfo = {
        hash: result.image_hash,
        url: imageApi.getImageUrl(slug, slideId, result.image_hash),
        content: content,
      };

      set((state) => ({
        images: [newImage, ...state.images.filter((img) => img.hash !== result.image_hash)],
        currentImageHash: result.image_hash,
        isGenerating: false,
      }));
    } catch (error: any) {
      set({ error: error.message, isGenerating: false });
      throw error;
    }
  },

  setCurrentImageHash: (hash: string | null) => {
    set({ currentImageHash: hash });
  },

  clearImages: () => {
    set({ images: [], currentImageHash: null });
  },
}));
