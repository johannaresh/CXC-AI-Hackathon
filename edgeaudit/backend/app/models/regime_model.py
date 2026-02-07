"""
Regime Model — GMM-based market regime detection and
per-regime strategy performance evaluation.
"""

import numpy as np
from sklearn.mixture import GaussianMixture

REGIME_LABELS = ["low_volatility", "normal", "high_volatility", "crisis"]


def _compute_rolling(returns: np.ndarray, window: int = 12):
    """Compute rolling mean and volatility for GMM features."""
    rolling_mean = np.array([
        np.mean(returns[max(0, i - window + 1):i + 1])
        for i in range(len(returns))
    ])
    rolling_vol = np.array([
        np.std(returns[max(0, i - window + 1):i + 1], ddof=1)
        if i >= 1 else 0.0
        for i in range(len(returns))
    ])
    return rolling_mean, rolling_vol


def _sharpe(returns: np.ndarray) -> float:
    if len(returns) < 2:
        return 0.0
    std = np.std(returns, ddof=1)
    if std < 1e-10:
        return 0.0
    return float(np.mean(returns) / std * np.sqrt(12))


def analyze_regimes(raw_returns: list[float]) -> dict:
    """Detect market regimes via GMM and compute regime sensitivity.

    Uses Gaussian Mixture Model on rolling volatility and rolling mean
    to cluster time periods into regimes, then evaluates strategy
    performance in each regime.

    Args:
        raw_returns: List of periodic strategy returns.

    Returns:
        Dict with regime analysis including per-regime Sharpe ratios.
    """
    returns = np.array(raw_returns, dtype=np.float64)
    n = len(returns)

    # Fallback for very short series
    if n < 12:
        overall_sharpe = _sharpe(returns) if n >= 2 else 0.0
        return {
            "current_regime": "insufficient_data",
            "regime_sensitivity": 0.0,
            "regimes_tested": ["insufficient_data"],
            "per_regime_sharpe": {"insufficient_data": overall_sharpe},
            "regime_proportions": {"insufficient_data": 1.0},
            "worst_regime_sharpe": overall_sharpe,
        }

    rolling_mean, rolling_vol = _compute_rolling(returns)

    # Build 2D feature matrix for GMM
    X = np.column_stack([rolling_vol, rolling_mean])

    # Skip leading zeros from rolling computation
    valid_start = min(12, n // 2)
    X_valid = X[valid_start:]
    returns_valid = returns[valid_start:]

    if len(X_valid) < 8:
        # Too few points for 4-component GMM — use 2-regime fallback
        return _two_regime_fallback(returns)

    # Fit GMM — use min(4, n_valid // 4) components to avoid overfitting
    n_components = min(4, max(2, len(X_valid) // 8))
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        random_state=42,
        n_init=3,
    )
    gmm.fit(X_valid)
    labels = gmm.predict(X_valid)

    # Sort components by mean volatility to assign regime names
    component_vols = [
        np.mean(X_valid[labels == c, 0]) for c in range(n_components)
    ]
    sorted_components = np.argsort(component_vols)
    regime_names = REGIME_LABELS[:n_components]

    # Map component index -> regime name
    component_to_regime = {}
    for rank, comp_idx in enumerate(sorted_components):
        component_to_regime[comp_idx] = regime_names[rank]

    # Compute per-regime Sharpe and proportions
    per_regime_sharpe = {}
    regime_proportions = {}
    for comp_idx in range(n_components):
        regime_name = component_to_regime[comp_idx]
        mask = labels == comp_idx
        regime_returns = returns_valid[mask]
        count = int(np.sum(mask))

        per_regime_sharpe[regime_name] = round(_sharpe(regime_returns), 4)
        regime_proportions[regime_name] = round(count / len(returns_valid), 4)

    # Current regime = regime of the most recent period
    current_regime = component_to_regime[labels[-1]]

    # Regime sensitivity = std of per-regime Sharpes / abs(overall Sharpe)
    overall_sharpe = _sharpe(returns_valid)
    sharpe_values = list(per_regime_sharpe.values())
    if abs(overall_sharpe) > 1e-10 and len(sharpe_values) > 1:
        regime_sensitivity = float(np.std(sharpe_values) / abs(overall_sharpe))
    else:
        regime_sensitivity = 0.0

    worst_regime_sharpe = min(sharpe_values) if sharpe_values else 0.0

    return {
        "current_regime": current_regime,
        "regime_sensitivity": round(regime_sensitivity, 4),
        "regimes_tested": regime_names,
        "per_regime_sharpe": per_regime_sharpe,
        "regime_proportions": regime_proportions,
        "worst_regime_sharpe": round(worst_regime_sharpe, 4),
    }


def _two_regime_fallback(returns: np.ndarray) -> dict:
    """Simple 2-regime split based on median volatility."""
    n = len(returns)
    window = min(6, n // 2)

    rolling_vol = np.array([
        np.std(returns[max(0, i - window + 1):i + 1], ddof=1)
        if i >= 1 else 0.0
        for i in range(n)
    ])

    median_vol = np.median(rolling_vol)
    low_mask = rolling_vol <= median_vol
    high_mask = ~low_mask

    low_sharpe = _sharpe(returns[low_mask]) if np.sum(low_mask) >= 2 else 0.0
    high_sharpe = _sharpe(returns[high_mask]) if np.sum(high_mask) >= 2 else 0.0

    regime_names = ["low_volatility", "high_volatility"]
    per_regime_sharpe = {
        "low_volatility": round(low_sharpe, 4),
        "high_volatility": round(high_sharpe, 4),
    }
    regime_proportions = {
        "low_volatility": round(float(np.mean(low_mask)), 4),
        "high_volatility": round(float(np.mean(high_mask)), 4),
    }

    current = "low_volatility" if low_mask[-1] else "high_volatility"
    overall = _sharpe(returns)
    sharpes = [low_sharpe, high_sharpe]
    if abs(overall) > 1e-10:
        sensitivity = float(np.std(sharpes) / abs(overall))
    else:
        sensitivity = 0.0

    return {
        "current_regime": current,
        "regime_sensitivity": round(sensitivity, 4),
        "regimes_tested": regime_names,
        "per_regime_sharpe": per_regime_sharpe,
        "regime_proportions": regime_proportions,
        "worst_regime_sharpe": round(min(sharpes), 4),
    }
