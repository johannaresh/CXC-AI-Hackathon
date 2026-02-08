from pydantic import BaseModel


class OverfitScore(BaseModel):
    probability: float
    confidence: float
    label: str  # "low", "medium", "high"


class RegimeAnalysis(BaseModel):
    current_regime: str
    regime_sensitivity: float
    regimes_tested: list[str]
    per_regime_sharpe: dict[str, float] = {}
    regime_proportions: dict[str, float] = {}
    worst_regime_sharpe: float = 0.0


class MonteCarloResult(BaseModel):
    simulated_sharpe_mean: float
    simulated_sharpe_std: float
    p_value: float
    num_simulations: int
    confidence_interval_95: list[float] = []
    sharpe_percentile: float = 0.0


class EdgeScoreBreakdown(BaseModel):
    edge_score: float
    overfit_sub_score: float
    regime_sub_score: float
    stat_sig_sub_score: float
    data_leakage_sub_score: float
    explainability_sub_score: float


class AuditResult(BaseModel):
    audit_id: str = ""
    strategy_name: str
    edge_score: EdgeScoreBreakdown | None = None
    overfit_score: OverfitScore
    regime_analysis: RegimeAnalysis
    monte_carlo: MonteCarloResult
    narrative: str
    recommendations: list[str]


class AuditSummary(BaseModel):
    """Lightweight audit summary for list view."""
    audit_id: str
    strategy_name: str
    edge_score: float
    overfit_probability: float
    overfit_label: str
    submitted_at: str


class AuditsListResponse(BaseModel):
    audits: list[AuditSummary]
    total: int
    page: int
    page_size: int


class AuditsSummaryResponse(BaseModel):
    total_audits: int
    unique_strategies: int
    average_edge_score: float
    average_overfit_probability: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    recent_audit_date: str | None = None
