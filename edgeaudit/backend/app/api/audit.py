import uuid

from fastapi import APIRouter, HTTPException

from ..schemas.strategy import StrategyPayload
from ..schemas.audit_result import (
    AuditResult,
    EdgeScoreBreakdown,
    MonteCarloResult,
    OverfitScore,
    RegimeAnalysis,
)
from ..services.feature_engineering import (
    build_feature_vector,
    feature_dict_to_array,
    FEATURE_NAMES,
)
from ..models.strategy_encoder import get_reconstruction_error
from ..models.overfit_classifier import predict_overfit
from ..models.regime_model import analyze_regimes
from ..services.monte_carlo import run_simulation
from ..services.edge_score import compute_edge_score, compute_data_leakage_score
from ..services.gemini_client import generate_narrative, generate_recommendations
from ..services.snowflake_client import store_audit_result
from ..services.backboard_client import push_audit_result as push_to_backboard

router = APIRouter()


@router.post("/audit", response_model=AuditResult)
def run_audit(payload: StrategyPayload):
    """Run a full audit on a submitted strategy.

    Pipeline: features -> VAE recon error -> overfit classifier ->
    regime model -> Monte Carlo -> edge score -> Gemini narrative ->
    Snowflake persistence -> Backboard push.
    """
    payload_dict = payload.model_dump()

    # Validate selected_asset if provided
    if payload.selected_asset:
        if payload.selected_asset not in payload.ticker_universe:
            raise HTTPException(
                status_code=400,
                detail=f"Selected asset '{payload.selected_asset}' is not in the strategy's ticker universe: {payload.ticker_universe}"
            )

    # 1. Feature engineering (20 features)
    features = build_feature_vector(payload_dict)

    # 2. VAE reconstruction error (anomaly signal)
    feature_array = [features[name] for name in FEATURE_NAMES]
    recon_error = get_reconstruction_error(feature_array)
    features["reconstruction_error"] = recon_error

    # 3. Overfit detection (XGBoost)
    overfit = predict_overfit(features)

    # 4. Regime analysis (GMM)
    regime = analyze_regimes(payload.raw_returns)

    # 5. Monte Carlo simulation (block bootstrap)
    mc = run_simulation(
        raw_returns=payload.raw_returns,
        observed_sharpe=payload.backtest_sharpe,
    )

    # 6. Edge Score aggregation
    leakage_score = compute_data_leakage_score(features)
    edge = compute_edge_score(
        overfit_probability=overfit["probability"],
        regime_sensitivity=regime["regime_sensitivity"],
        mc_p_value=mc["p_value"],
        data_leakage_score=leakage_score,
        reconstruction_error=recon_error,
    )

    # 7. LLM narrative + recommendations
    audit_data = {
        "strategy_name": payload.name,
        "overfit": overfit,
        "regime": regime,
        "monte_carlo": mc,
        "edge_score": edge,
        "payload": payload_dict,
        "selected_asset": payload.selected_asset,  # Pass to narrative generation
    }
    narrative = generate_narrative(audit_data)
    recommendations = generate_recommendations(audit_data)

    # 8. Build result
    result = AuditResult(
        audit_id=str(uuid.uuid4()),
        strategy_name=payload.name,
        edge_score=EdgeScoreBreakdown(**edge),
        overfit_score=OverfitScore(**overfit),
        regime_analysis=RegimeAnalysis(**regime),
        monte_carlo=MonteCarloResult(**mc),
        narrative=narrative,
        recommendations=recommendations,
    )

    # 9. Persist to Snowflake (non-blocking — failures don't break the response)
    result_dict = result.model_dump()
    result_dict["features"] = features
    result_dict["selected_asset"] = payload.selected_asset  # Include for Snowflake and Backboard
    stored_id = store_audit_result(result_dict, payload_dict)
    if stored_id:
        result.audit_id = stored_id

    # 10. Push to Backboard.io for dashboard visualization
    push_to_backboard(result_dict)

    return result
