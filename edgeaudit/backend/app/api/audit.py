import uuid

from typing import Optional
from fastapi import APIRouter, HTTPException

from ..schemas.strategy import StrategyPayload
from ..schemas.audit_result import (
    AuditResult,
    AuditSummary,
    AuditsListResponse,
    AuditsSummaryResponse,
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


@router.get("/audit/{audit_id}", response_model=AuditResult)
def get_audit(audit_id: str):
    """Retrieve a specific audit result by ID.

    Used by Backboard to display individual audit reports.
    """
    import json
    from ..services.snowflake_client import get_audit_by_id

    audit = get_audit_by_id(audit_id)
    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit with ID '{audit_id}' not found"
        )

    # Parse JSON fields (stored as VARIANT in Snowflake)
    recommendations = audit.get("RECOMMENDATIONS", [])
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except json.JSONDecodeError:
            recommendations = []

    # Transform Snowflake dict to AuditResult schema
    return AuditResult(
        audit_id=audit.get("AUDIT_ID", ""),
        strategy_name=audit.get("STRATEGY_NAME", ""),
        edge_score=EdgeScoreBreakdown(
            edge_score=audit.get("EDGE_SCORE", 0.0),
            overfit_sub_score=audit.get("OVERFIT_SUB_SCORE", 0.0),
            regime_sub_score=audit.get("REGIME_SUB_SCORE", 0.0),
            stat_sig_sub_score=audit.get("STAT_SIG_SUB_SCORE", 0.0),
            data_leakage_sub_score=audit.get("DATA_LEAKAGE_SUB_SCORE", 0.0),
            explainability_sub_score=audit.get("EXPLAIN_SUB_SCORE", 0.0),
        ),
        overfit_score=OverfitScore(
            probability=audit.get("OVERFIT_PROBABILITY", 0.0),
            confidence=audit.get("OVERFIT_CONFIDENCE", 0.0),
            label=audit.get("OVERFIT_LABEL", "medium"),
        ),
        regime_analysis=RegimeAnalysis(
            current_regime=audit.get("REGIME_CURRENT", "unknown"),
            regime_sensitivity=audit.get("REGIME_SENSITIVITY", 0.0),
            regimes_tested=[],  # Not stored in Snowflake
            per_regime_sharpe={},  # Not stored in Snowflake
            regime_proportions={},  # Not stored in Snowflake
            worst_regime_sharpe=0.0,  # Not stored in Snowflake
        ),
        monte_carlo=MonteCarloResult(
            simulated_sharpe_mean=audit.get("MC_SHARPE_MEAN", 0.0),
            simulated_sharpe_std=audit.get("MC_SHARPE_STD", 0.0),
            p_value=audit.get("MC_P_VALUE", 0.0),
            num_simulations=audit.get("MC_NUM_SIMULATIONS", 0),
            confidence_interval_95=[],  # Not stored in Snowflake
            sharpe_percentile=0.0,  # Not stored in Snowflake
        ),
        narrative=audit.get("NARRATIVE", ""),
        recommendations=recommendations if isinstance(recommendations, list) else [],
    )


@router.get("/audits", response_model=AuditsListResponse)
def list_audits(
    page: int = 1,
    page_size: int = 50,
    strategy_name: Optional[str] = None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc"
):
    """List all audits with pagination and filtering.

    Query params:
    - page: Page number (1-indexed, default: 1)
    - page_size: Results per page (max 100, default: 50)
    - strategy_name: Filter by strategy name (optional)
    - sort_by: Column to sort by (submitted_at, edge_score, overfit_probability)
    - sort_order: Sort direction (asc, desc)
    """
    from ..services.snowflake_client import list_all_audits

    # Validate inputs
    page = max(1, page)
    page_size = min(100, max(1, page_size))

    if sort_by not in ["submitted_at", "edge_score", "overfit_probability"]:
        sort_by = "submitted_at"

    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    # Fetch from Snowflake
    result = list_all_audits(
        page=page,
        page_size=page_size,
        strategy_name=strategy_name,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return AuditsListResponse(**result)


@router.get("/audits/summary", response_model=AuditsSummaryResponse)
def get_audits_summary():
    """Get aggregated KPIs for dashboard display."""
    from ..services.snowflake_client import get_audit_summary

    summary = get_audit_summary()
    if not summary:
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch audit summary from Snowflake"
        )

    return AuditsSummaryResponse(**summary)


@router.get("/strategies/available")
def get_available_strategies():
    """Get list of available strategies from training data for quick selection."""
    import json
    from pathlib import Path

    # Load training strategies from JSON file
    strategies_file = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "training_strategies.json"

    if not strategies_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Strategies file not found"
        )

    try:
        with open(strategies_file, "r", encoding="utf-8") as f:
            strategies = json.load(f)

        # Return simplified list with name and assets for selection UI
        return {
            "strategies": [
                {
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "assets": s.get("ticker_universe", []),
                    "backtest_sharpe": s.get("backtest_sharpe", 0),
                }
                for s in strategies
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load strategies: {str(e)}"
        )


@router.get("/strategies/{strategy_name}")
def get_strategy_by_name(strategy_name: str):
    """Get full strategy data by name for audit submission."""
    import json
    from pathlib import Path

    strategies_file = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "training_strategies.json"

    if not strategies_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Strategies file not found"
        )

    try:
        with open(strategies_file, "r", encoding="utf-8") as f:
            strategies = json.load(f)

        # Find matching strategy
        for strategy in strategies:
            if strategy.get("name") == strategy_name:
                return strategy

        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load strategy: {str(e)}"
        )
