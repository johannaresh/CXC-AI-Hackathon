from fastapi import APIRouter

from backend.app.schemas.strategy import StrategyPayload
from backend.app.schemas.audit_result import (
    AuditResult,
    MonteCarloResult,
    OverfitScore,
    RegimeAnalysis,
)
from backend.app.services.feature_engineering import build_feature_vector
from backend.app.models.overfit_classifier import predict_overfit
from backend.app.models.regime_model import analyze_regimes
from backend.app.services.monte_carlo import run_simulation
from backend.app.services.gemini_client import generate_narrative, generate_recommendations

router = APIRouter()


@router.post("/audit", response_model=AuditResult)
def run_audit(payload: StrategyPayload):
    """Run a full audit on a submitted strategy.

    TODO: Wire in real ML models and Snowflake data.
    TODO: Add async support for long-running audits.
    TODO: Store audit results for historical tracking.
    """
    # 1. Feature engineering
    features = build_feature_vector(payload.model_dump())

    # 2. Overfit detection
    overfit = predict_overfit(features)

    # 3. Regime analysis
    regime = analyze_regimes(payload.raw_returns)

    # 4. Monte Carlo simulation
    mc = run_simulation(
        raw_returns=payload.raw_returns,
        observed_sharpe=payload.backtest_sharpe,
    )

    # 5. LLM narrative
    audit_data = {
        "strategy_name": payload.name,
        "overfit": overfit,
        "regime": regime,
        "monte_carlo": mc,
    }
    narrative = generate_narrative(audit_data)
    recommendations = generate_recommendations(audit_data)

    return AuditResult(
        strategy_name=payload.name,
        overfit_score=OverfitScore(**overfit),
        regime_analysis=RegimeAnalysis(**regime),
        monte_carlo=MonteCarloResult(**mc),
        narrative=narrative,
        recommendations=recommendations,
    )
