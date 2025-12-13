export enum TicketStatus {
  OPEN = 'open',
  DONE = 'done',
}

export interface Tag {
  id: string;
  name: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  title: string;
  description: string | null;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  tags: Tag[];
}

export interface TicketsListResponse {
  total: number;
  items: Ticket[];
}

export interface TicketCreate {
  title: string;
  description?: string | null;
  tags?: string[];
}

export interface TicketUpdate {
  title?: string;
  description?: string | null;
  status?: TicketStatus;
  tags?: string[];
}

export interface TagCreate {
  name: string;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface ListTicketsParams {
  status?: TicketStatus | null;
  tags?: string[];
  q?: string | null;
  limit?: number;
  offset?: number;
}

export interface ListTagsParams {
  q?: string | null;
}
