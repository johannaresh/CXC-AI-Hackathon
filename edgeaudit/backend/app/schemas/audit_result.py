from pydantic import BaseModel


class OverfitScore(BaseModel):
    probability: float
    confidence: float
    label: str  # "low", "medium", "high"


class RegimeAnalysis(BaseModel):
    current_regime: str
    regime_sensitivity: float
    regimes_tested: list[str]


class MonteCarloResult(BaseModel):
    simulated_sharpe_mean: float
    simulated_sharpe_std: float
    p_value: float
    num_simulations: int


class AuditResult(BaseModel):
    strategy_name: str
    overfit_score: OverfitScore
    regime_analysis: RegimeAnalysis
    monte_carlo: MonteCarloResult
    narrative: str
    recommendations: list[str]
