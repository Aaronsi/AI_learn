export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface ApiError {
  message: string;
  status?: number;
}

export interface CreateSlideRequest {
  content: string;
  position?: number;
}

export interface UpdateSlideRequest {
  content?: string;
}

export interface ReorderSlidesRequest {
  slide_ids: string[];
}

export interface GenerateImageResponse {
  image_hash: string;
  cost: number;
  message?: string;
}
