"""
Feature Engineering — transforms raw strategy metadata and returns
into a 20-dimensional feature vector for ML model consumption.
"""

import numpy as np
from scipy.stats import skew, kurtosis


def _lag1_autocorrelation(returns: np.ndarray) -> float:
    """Compute lag-1 autocorrelation of return series."""
    if len(returns) < 3:
        return 0.0
    return float(np.corrcoef(returns[:-1], returns[1:])[0, 1])


def _max_consecutive(returns: np.ndarray, positive: bool) -> int:
    """Longest streak of consecutive positive (or negative) returns."""
    if len(returns) == 0:
        return 0
    mask = returns > 0 if positive else returns < 0
    max_streak = 0
    current = 0
    for val in mask:
        if val:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def _hurst_exponent(returns: np.ndarray) -> float:
    """Estimate Hurst exponent via rescaled range (R/S) analysis."""
    n = len(returns)
    if n < 20:
        return 0.5  # default: random walk

    max_k = min(n // 2, 100)
    sizes = []
    rs_values = []

    for size in [int(n / d) for d in range(2, min(10, n // 10 + 1)) if n // d >= 8]:
        if size < 8:
            continue
        rs_list = []
        for start in range(0, n - size + 1, size):
            segment = returns[start:start + size]
            mean_seg = np.mean(segment)
            deviate = np.cumsum(segment - mean_seg)
            r = np.max(deviate) - np.min(deviate)
            s = np.std(segment, ddof=1)
            if s > 1e-10:
                rs_list.append(r / s)
        if rs_list:
            sizes.append(size)
            rs_values.append(np.mean(rs_list))

    if len(sizes) < 2:
        return 0.5

    log_sizes = np.log(sizes)
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_sizes, log_rs, 1)
    return float(np.clip(slope, 0.0, 1.0))


def _rolling_sharpe_std(returns: np.ndarray, window: int = 12) -> float:
    """Standard deviation of rolling Sharpe ratios (high = fragile)."""
    if len(returns) < window + 2:
        return 0.0
    sharpes = []
    for i in range(len(returns) - window + 1):
        seg = returns[i:i + window]
        std = np.std(seg, ddof=1)
        if std > 1e-10:
            sharpes.append(np.mean(seg) / std)
    if len(sharpes) < 2:
        return 0.0
    return float(np.std(sharpes))


def _tail_ratio(returns: np.ndarray) -> float:
    """Ratio of upper tail to lower tail magnitude."""
    if len(returns) < 5:
        return 1.0
    upper = np.abs(np.percentile(returns, 95))
    lower = np.abs(np.percentile(returns, 5))
    if lower < 1e-10:
        return 10.0
    return float(upper / lower)


def _sortino_ratio(returns: np.ndarray) -> float:
    """Mean return / downside deviation."""
    if len(returns) < 2:
        return 0.0
    mean_r = np.mean(returns)
    downside = returns[returns < 0]
    if len(downside) < 1:
        return 10.0  # no downside
    downside_std = np.std(downside, ddof=1)
    if downside_std < 1e-10:
        return 10.0
    return float(mean_r / downside_std * np.sqrt(12))


def _calmar_ratio(returns: np.ndarray, max_drawdown: float) -> float:
    """Annualized return / abs(max drawdown)."""
    if abs(max_drawdown) < 1e-10:
        return 10.0
    annualized = float(np.mean(returns) * 12)
    return float(annualized / abs(max_drawdown))


def build_feature_vector(payload: dict) -> dict:
    """Compute 20 engineered features from a strategy payload.

    Args:
        payload: Raw strategy payload as a dict.

    Returns:
        Dict of 20 named features.
    """
    returns = np.array(payload.get("raw_returns", []), dtype=np.float64)
    n = len(returns)
    num_params = payload.get("num_parameters", 0)
    split_ratio = payload.get("train_test_split_ratio", 0.7)
    backtest_sharpe = payload.get("backtest_sharpe", 0.0)
    backtest_mdd = payload.get("backtest_max_drawdown", 0.0)

    if n == 0:
        return {
            "mean_return": 0.0,
            "std_return": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
            "num_parameters": num_params,
            "train_test_split_ratio": split_ratio,
            "param_to_obs_ratio": 0.0,
            "backtest_sharpe": backtest_sharpe,
            "backtest_max_drawdown": backtest_mdd,
            "sharpe_to_param_ratio": 0.0,
            "return_autocorrelation": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "hurst_exponent": 0.5,
            "rolling_sharpe_std": 0.0,
            "tail_ratio": 1.0,
            "calmar_ratio": 0.0,
            "sortino_ratio": 0.0,
            "sample_size": 0,
            "reconstruction_error": 0.0,
        }

    mean_r = float(np.mean(returns))
    std_r = float(np.std(returns, ddof=1)) if n > 1 else 0.0

    return {
        "mean_return": mean_r,
        "std_return": std_r,
        "skew": float(skew(returns)) if n > 2 else 0.0,
        "kurtosis": float(kurtosis(returns)) if n > 3 else 0.0,
        "num_parameters": num_params,
        "train_test_split_ratio": split_ratio,
        "param_to_obs_ratio": num_params / n if n > 0 else 0.0,
        "backtest_sharpe": backtest_sharpe,
        "backtest_max_drawdown": backtest_mdd,
        "sharpe_to_param_ratio": backtest_sharpe / num_params if num_params > 0 else 0.0,
        "return_autocorrelation": _lag1_autocorrelation(returns),
        "max_consecutive_wins": _max_consecutive(returns, positive=True),
        "max_consecutive_losses": _max_consecutive(returns, positive=False),
        "hurst_exponent": _hurst_exponent(returns),
        "rolling_sharpe_std": _rolling_sharpe_std(returns),
        "tail_ratio": _tail_ratio(returns),
        "calmar_ratio": _calmar_ratio(returns, backtest_mdd),
        "sortino_ratio": _sortino_ratio(returns),
        "sample_size": n,
        "reconstruction_error": 0.0,  # populated later by VAE encoder
    }


# Ordered list of feature names for ML model input
FEATURE_NAMES = [
    "mean_return", "std_return", "skew", "kurtosis",
    "num_parameters", "train_test_split_ratio",
    "param_to_obs_ratio", "backtest_sharpe", "backtest_max_drawdown",
    "sharpe_to_param_ratio", "return_autocorrelation",
    "max_consecutive_wins", "max_consecutive_losses",
    "hurst_exponent", "rolling_sharpe_std", "tail_ratio",
    "calmar_ratio", "sortino_ratio", "sample_size",
    "reconstruction_error",
]


def feature_dict_to_array(features: dict) -> np.ndarray:
    """Convert feature dict to ordered numpy array for ML models."""
    return np.array([features[name] for name in FEATURE_NAMES], dtype=np.float64)
