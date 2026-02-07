"""
Regime Model — scikit-learn model that identifies market regimes
and evaluates how sensitive a strategy is to regime changes.
"""


def analyze_regimes(raw_returns: list[float]) -> dict:
    """Detect market regimes and compute regime sensitivity.

    TODO: Implement HMM or GMM-based regime detection using scikit-learn.
    TODO: Compute strategy performance per regime.
    TODO: Replace mock with real inference.

    Args:
        raw_returns: List of periodic strategy returns.

    Returns:
        Dict with current_regime, regime_sensitivity, and regimes_tested.
    """
    # --- Mock implementation ---
    return {
        "current_regime": "low_volatility",
        "regime_sensitivity": 0.35,
        "regimes_tested": ["low_volatility", "high_volatility", "crisis", "recovery"],
    }
