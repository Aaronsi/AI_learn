import apiClient from './api';
import type { GenerateStyleRequest, GenerateStyleResponse, SelectStyleRequest } from '@/types/style';
import type { SlidesProject } from '@/types/slide';

/**
 * Generate style candidates
 */
export async function generateStyleCandidates(
  slug: string,
  data: GenerateStyleRequest
): Promise<GenerateStyleResponse> {
  const response = await apiClient.post<GenerateStyleResponse>(
    `/slides/${slug}/style/generate`,
    data
  );
  return response.data;
}

/**
 * Select a style from candidates
 */
export async function selectStyle(
  slug: string,
  data: SelectStyleRequest
): Promise<SlidesProject> {
  const response = await apiClient.post<SlidesProject>(`/slides/${slug}/style/select`, data);
  return response.data;
}
