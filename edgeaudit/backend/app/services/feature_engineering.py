"""
Feature Engineering — transforms raw strategy metadata and returns
into a feature vector suitable for ML model consumption.
"""

import numpy as np


def build_feature_vector(payload: dict) -> dict:
    """Compute engineered features from a strategy payload.

    TODO: Add rolling Sharpe, Sortino, Calmar ratios.
    TODO: Add parameter-count-to-sample-size ratio.
    TODO: Add autocorrelation features.

    Args:
        payload: Raw strategy payload as a dict.

    Returns:
        Dict of named features.
    """
    returns = np.array(payload.get("raw_returns", []))

    if len(returns) == 0:
        return {
            "mean_return": 0.0,
            "std_return": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
            "num_parameters": payload.get("num_parameters", 0),
            "train_test_split_ratio": payload.get("train_test_split_ratio", 0.7),
        }

    from scipy.stats import skew, kurtosis

    return {
        "mean_return": float(np.mean(returns)),
        "std_return": float(np.std(returns)),
        "skew": float(skew(returns)),
        "kurtosis": float(kurtosis(returns)),
        "num_parameters": payload.get("num_parameters", 0),
        "train_test_split_ratio": payload.get("train_test_split_ratio", 0.7),
    }
