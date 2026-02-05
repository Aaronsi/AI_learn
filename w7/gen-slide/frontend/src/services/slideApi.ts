import apiClient from './api';
import type { SlidesProject, Slide } from '@/types/slide';
import type { CreateSlideRequest, UpdateSlideRequest, ReorderSlidesRequest } from '@/types/api';

/**
 * Get project by slug
 */
export async function getProject(slug: string): Promise<SlidesProject> {
  const response = await apiClient.get<SlidesProject>(`/slides/${slug}`);
  return response.data;
}

/**
 * Create a new project
 */
export async function createProject(slug: string, title: string): Promise<SlidesProject> {
  const response = await apiClient.post<SlidesProject>(`/slides/${slug}`, { slug, title });
  return response.data;
}

/**
 * Update project title
 */
export async function updateProjectTitle(slug: string, title: string): Promise<SlidesProject> {
  const response = await apiClient.put<SlidesProject>(`/slides/${slug}`, { title });
  return response.data;
}

/**
 * Create a new slide
 */
export async function createSlide(slug: string, data: CreateSlideRequest): Promise<Slide> {
  const response = await apiClient.post<Slide>(`/slides/${slug}/slides`, data);
  return response.data;
}

/**
 * Update slide content
 */
export async function updateSlide(
  slug: string,
  slideId: string,
  data: UpdateSlideRequest
): Promise<Slide> {
  const response = await apiClient.put<Slide>(`/slides/${slug}/slides/${slideId}`, data);
  return response.data;
}

/**
 * Delete a slide
 */
export async function deleteSlide(slug: string, slideId: string): Promise<void> {
  await apiClient.delete(`/slides/${slug}/slides/${slideId}`);
}

/**
 * Reorder slides
 */
export async function reorderSlides(slug: string, data: ReorderSlidesRequest): Promise<void> {
  await apiClient.put(`/slides/${slug}/reorder`, data);
}
