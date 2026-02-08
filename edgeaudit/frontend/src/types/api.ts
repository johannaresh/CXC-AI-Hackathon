export interface ApiError {
  detail: string;
}

export interface QueryParams {
  page?: number;
  page_size?: number;
  strategy_name?: string;
  sort_by?: 'submitted_at' | 'edge_score' | 'overfit_probability';
  sort_order?: 'asc' | 'desc';
}
