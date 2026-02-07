import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.services.feature_engineering import (
    build_feature_vector,
    FEATURE_NAMES,
    feature_dict_to_array,
)


def _sample_payload(n_returns=60):
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, n_returns).tolist()
    return {
        "name": "TestStrat",
        "backtest_sharpe": 1.5,
        "backtest_max_drawdown": -0.15,
        "backtest_start_date": "2018-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": 5,
        "train_test_split_ratio": 0.7,
        "rebalance_frequency": "monthly",
        "raw_returns": returns,
    }


def test_build_feature_vector_returns_20_features():
    feat = build_feature_vector(_sample_payload())
    assert len(feat) == 20
    for name in FEATURE_NAMES:
        assert name in feat, f"Missing feature: {name}"


def test_build_feature_vector_empty_returns():
    payload = _sample_payload()
    payload["raw_returns"] = []
    feat = build_feature_vector(payload)
    assert feat["mean_return"] == 0.0
    assert feat["sample_size"] == 0
    assert feat["hurst_exponent"] == 0.5


def test_build_feature_vector_single_return():
    payload = _sample_payload()
    payload["raw_returns"] = [0.01]
    feat = build_feature_vector(payload)
    assert feat["sample_size"] == 1
    assert feat["mean_return"] == 0.01


def test_param_to_obs_ratio():
    payload = _sample_payload(n_returns=50)
    payload["num_parameters"] = 10
    feat = build_feature_vector(payload)
    assert abs(feat["param_to_obs_ratio"] - 10 / 50) < 1e-10


def test_hurst_exponent_range():
    feat = build_feature_vector(_sample_payload(n_returns=100))
    assert 0.0 <= feat["hurst_exponent"] <= 1.0


def test_feature_dict_to_array():
    feat = build_feature_vector(_sample_payload())
    arr = feature_dict_to_array(feat)
    assert arr.shape == (20,)
    assert arr.dtype == np.float64


def test_tail_ratio_positive():
    feat = build_feature_vector(_sample_payload())
    assert feat["tail_ratio"] > 0


def test_sortino_ratio_computed():
    feat = build_feature_vector(_sample_payload())
    # With mixed positive/negative returns, sortino should be finite
    assert np.isfinite(feat["sortino_ratio"])
