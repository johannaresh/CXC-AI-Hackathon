export interface EdgeScoreBreakdown {
  edge_score: number;
  overfit_sub_score: number;
  regime_sub_score: number;
  stat_sig_sub_score: number;
  data_leakage_sub_score: number;
  explainability_sub_score: number;
}

export interface OverfitScore {
  probability: number;
  confidence: number;
  label: 'low' | 'medium' | 'high';
}

export interface RegimeAnalysis {
  current_regime: string;
  regime_sensitivity: number;
  regimes_tested: string[];
  per_regime_sharpe: Record<string, number>;
  regime_proportions?: Record<string, number>;
  worst_regime_sharpe: number;
}

export interface MonteCarloResult {
  simulated_sharpe_mean: number;
  simulated_sharpe_std: number;
  p_value: number;
  num_simulations: number;
  confidence_interval_95: number[];
  sharpe_percentile: number;
}

export interface AuditResult {
  audit_id: string;
  strategy_name: string;
  edge_score: EdgeScoreBreakdown;
  overfit_score: OverfitScore;
  regime_analysis: RegimeAnalysis;
  monte_carlo: MonteCarloResult;
  narrative: string;
  recommendations: string[];
}

export interface AuditSummary {
  audit_id: string;
  strategy_name: string;
  edge_score: number;
  overfit_probability: number;
  overfit_label: 'low' | 'medium' | 'high';
  submitted_at: string;
}

export interface AuditsListResponse {
  audits: AuditSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditsSummaryResponse {
  total_audits: number;
  unique_strategies: number;
  average_edge_score: number;
  average_overfit_probability: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  recent_audit_date: string | null;
}
