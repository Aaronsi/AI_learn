export interface Style {
  prompt: string;
  image: string;
}

export interface Slide {
  sid: string;
  content: string;
  created_at: string;
  updated_at: string;
  current_image_hash: string;
  has_matching_image: boolean;
}

export interface SlidesProject {
  slug: string;
  title: string;
  style: Style | null;
  slides: Slide[];
  total_cost: number;
}

export interface SlideImage {
  hash: string;
  url: string;
  is_current: boolean;
  created_at: string;
}
