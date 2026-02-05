import { create } from 'zustand';
import type { SlidesProject, Slide } from '@/types/slide';
import * as slideApi from '@/services/slideApi';

interface SlideStore {
  project: SlidesProject | null;
  selectedSlideId: string | null;
  selectedSlide: Slide | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadProject: (slug: string) => Promise<void>;
  createProject: (slug: string, title: string) => Promise<void>;
  selectSlide: (slideId: string | null) => void;
  updateSlide: (slideId: string, content: string) => Promise<void>;
  addSlide: (content: string, position?: number) => Promise<void>;
  deleteSlide: (slideId: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;
  updateProjectTitle: (title: string) => Promise<void>;
  setProject: (project: SlidesProject) => void;
}

export const useSlideStore = create<SlideStore>((set, get) => ({
  project: null,
  selectedSlideId: null,
  get selectedSlide() {
    const state = get();
    if (!state.project || !state.selectedSlideId) return null;
    return state.project.slides.find(s => s.sid === state.selectedSlideId) || null;
  },
  isLoading: false,
  error: null,

  loadProject: async (slug: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await slideApi.getProject(slug);
      set({
        project,
        isLoading: false,
        selectedSlideId: project.slides.length > 0 ? project.slides[0].sid : null
      });
    } catch (error: any) {
      console.log('Error loading project:', error);
      // Handle ApiError from interceptor (has status directly) or AxiosError (has response.status)
      const status = error?.status || error?.response?.status;

      // If project doesn't exist (404), set a special error
      if (status === 404) {
        set({ error: 'PROJECT_NOT_FOUND', isLoading: false });
      } else {
        set({ error: error?.message || 'Failed to load project', isLoading: false });
      }
    }
  },

  createProject: async (slug: string, title: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await slideApi.createProject(slug, title);
      set({
        project,
        isLoading: false,
        selectedSlideId: null
      });
    } catch (error: any) {
      const status = error?.status || error?.response?.status;
      // If project already exists (409), try to load it instead
      if (status === 409) {
        try {
          const project = await slideApi.getProject(slug);
          set({
            project,
            isLoading: false,
            selectedSlideId: project.slides.length > 0 ? project.slides[0].sid : null
          });
          return;
        } catch (loadError: any) {
          // If loading also fails, throw the original error
          set({ error: error.message || 'Failed to create project', isLoading: false });
          throw error;
        }
      }
      set({ error: error.message || 'Failed to create project', isLoading: false });
      throw error;
    }
  },

  selectSlide: (slideId: string | null) => {
    set({ selectedSlideId: slideId });
  },

  updateSlide: async (slideId: string, content: string) => {
    const { project } = get();
    if (!project) return;

    try {
      const updatedSlide = await slideApi.updateSlide(project.slug, slideId, { content });

      set({
        project: {
          ...project,
          slides: project.slides.map((slide) =>
            slide.sid === slideId ? updatedSlide : slide
          ),
        },
      });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  addSlide: async (content: string, position?: number) => {
    const { project } = get();
    if (!project) return;

    try {
      const newSlide = await slideApi.createSlide(project.slug, { content, position });

      const slides = [...project.slides];
      if (position !== undefined && position >= 0 && position <= slides.length) {
        slides.splice(position, 0, newSlide);
      } else {
        slides.push(newSlide);
      }

      set({
        project: {
          ...project,
          slides,
        },
        selectedSlideId: newSlide.sid,
      });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  deleteSlide: async (slideId: string) => {
    const { project, selectedSlideId } = get();
    if (!project) return;

    try {
      await slideApi.deleteSlide(project.slug, slideId);

      const slides = project.slides.filter((slide) => slide.sid !== slideId);
      let newSelectedId = selectedSlideId;

      if (selectedSlideId === slideId) {
        newSelectedId = slides.length > 0 ? slides[0].sid : null;
      }

      set({
        project: {
          ...project,
          slides,
        },
        selectedSlideId: newSelectedId,
      });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  reorderSlides: async (slideIds: string[]) => {
    const { project } = get();
    if (!project) return;

    try {
      await slideApi.reorderSlides(project.slug, { slide_ids: slideIds });

      const slideMap = new Map(project.slides.map((slide) => [slide.sid, slide]));
      const reorderedSlides = slideIds.map((id) => slideMap.get(id)!).filter(Boolean);

      set({
        project: {
          ...project,
          slides: reorderedSlides,
        },
      });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  updateProjectTitle: async (title: string) => {
    const { project } = get();
    if (!project) return;

    try {
      const updatedProject = await slideApi.updateProjectTitle(project.slug, title);
      set({ project: updatedProject });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  setProject: (project: SlidesProject) => {
    set({ project });
  },
}));
