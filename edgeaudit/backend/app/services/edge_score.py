"""
Edge Score Aggregator — combines ML model outputs into a composite
0-100 Edge Score with 5 sub-scores.
"""


def compute_data_leakage_score(features: dict) -> float:
    """Rule-based scoring for common data leakage patterns.

    Returns 0-100 (100 = no leakage risk detected).
    """
    score = 100.0

    split_ratio = features.get("train_test_split_ratio", 0.7)
    sharpe = features.get("backtest_sharpe", 0.0)
    num_params = features.get("num_parameters", 0)
    sample_size = features.get("sample_size", 0)
    std_return = features.get("std_return", 0.0)
    param_obs_ratio = features.get("param_to_obs_ratio", 0.0)

    # Penalty: very high train/test split ratio (tiny test set)
    if split_ratio > 0.9:
        score -= 30
    elif split_ratio > 0.8:
        score -= 15

    # Penalty: unrealistic Sharpe for the parameter count
    if sharpe > 2.0 and num_params > 10:
        score -= 25
    elif sharpe > 3.0:
        score -= 20

    # Penalty: very short sample
    if sample_size > 0 and sample_size < 36:
        score -= 20
    elif 0 < sample_size < 60:
        score -= 10

    # Penalty: suspiciously low volatility with high Sharpe
    if std_return < 0.005 and sharpe > 1.5:
        score -= 20

    # Penalty: high parameter-to-observation ratio
    if param_obs_ratio > 0.15:
        score -= 25
    elif param_obs_ratio > 0.08:
        score -= 10

    return max(0.0, score)


def compute_edge_score(
    overfit_probability: float,
    regime_sensitivity: float,
    mc_p_value: float,
    data_leakage_score: float,
    reconstruction_error: float,
    reconstruction_error_scale: float = 50.0,
) -> dict:
    """Compute composite Edge Score (0-100) from ML outputs.

    Higher score = more likely the strategy has genuine edge.

    Sub-score weights:
        Overfit Risk:              30%
        Regime Robustness:         20%
        Statistical Significance:  25%
        Data Leakage Risk:         15%
        Explainability:            10%

    Args:
        overfit_probability: P(overfit) from XGBoost (0-1).
        regime_sensitivity: Regime sensitivity from GMM (0+).
        mc_p_value: p-value from Monte Carlo bootstrap (0-1).
        data_leakage_score: Leakage score (0-100).
        reconstruction_error: VAE reconstruction MSE.
        reconstruction_error_scale: Scaling factor for recon error.

    Returns:
        Dict with edge_score and 5 sub-scores.
    """
    overfit_sub = (1.0 - overfit_probability) * 100.0
    regime_sub = max(0.0, 100.0 - regime_sensitivity * 100.0)
    stat_sig_sub = (1.0 - mc_p_value) * 100.0
    leakage_sub = data_leakage_score
    explain_sub = max(0.0, 100.0 - reconstruction_error * reconstruction_error_scale)

    # Clamp all sub-scores to [0, 100]
    overfit_sub = max(0.0, min(100.0, overfit_sub))
    regime_sub = max(0.0, min(100.0, regime_sub))
    stat_sig_sub = max(0.0, min(100.0, stat_sig_sub))
    leakage_sub = max(0.0, min(100.0, leakage_sub))
    explain_sub = max(0.0, min(100.0, explain_sub))

    edge_score = (
        0.30 * overfit_sub
        + 0.20 * regime_sub
        + 0.25 * stat_sig_sub
        + 0.15 * leakage_sub
        + 0.10 * explain_sub
    )

    return {
        "edge_score": round(edge_score, 1),
        "overfit_sub_score": round(overfit_sub, 1),
        "regime_sub_score": round(regime_sub, 1),
        "stat_sig_sub_score": round(stat_sig_sub, 1),
        "data_leakage_sub_score": round(leakage_sub, 1),
        "explainability_sub_score": round(explain_sub, 1),
    }
