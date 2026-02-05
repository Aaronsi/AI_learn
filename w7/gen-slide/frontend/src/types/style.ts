export interface StyleCandidate {
  image: string;
  prompt: string;
}

export interface GenerateStyleRequest {
  prompt: string;
}

export interface GenerateStyleResponse {
  candidates: StyleCandidate[];
}

export interface SelectStyleRequest {
  prompt: string;
  image: string;
}
