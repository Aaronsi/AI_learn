import apiClient from './api';
import type { GenerateImageResponse } from '@/types/api';

/**
 * Get all images for a slide
 */
export async function getSlideImages(slug: string, slideId: string): Promise<string[]> {
  const response = await apiClient.get<string[]>(`/slides/${slug}/images/${slideId}`);
  return response.data;
}

/**
 * Generate image for a slide
 */
export async function generateImage(
  slug: string,
  slideId: string
): Promise<GenerateImageResponse> {
  const response = await apiClient.post<GenerateImageResponse>(
    `/slides/${slug}/generate/${slideId}`
  );
  return response.data;
}

/**
 * Get image URL by hash
 */
export function getImageUrl(slug: string, slideId: string, hash: string): string {
  return `http://localhost:8000/api/slides/${slug}/images/${slideId}/${hash}.jpg`;
}

/**
 * Get style image URL
 */
export function getStyleImageUrl(slug: string): string {
  return `http://localhost:8000/api/slides/${slug}/style`;
}

/**
 * Check if a string is a base64 image data URL
 */
export function isBase64Image(str: string): boolean {
  return str.startsWith('data:image/') || (str.length > 100 && !str.includes('/') && !str.includes('\\'));
}
