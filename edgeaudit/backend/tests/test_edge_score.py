import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.edge_score import compute_edge_score, compute_data_leakage_score


def test_edge_score_range():
    result = compute_edge_score(
        overfit_probability=0.5,
        regime_sensitivity=0.5,
        mc_p_value=0.5,
        data_leakage_score=50.0,
        reconstruction_error=0.5,
    )
    assert 0 <= result["edge_score"] <= 100


def test_perfect_strategy_high_score():
    result = compute_edge_score(
        overfit_probability=0.05,
        regime_sensitivity=0.1,
        mc_p_value=0.01,
        data_leakage_score=95.0,
        reconstruction_error=0.01,
    )
    assert result["edge_score"] >= 80


def test_terrible_strategy_low_score():
    result = compute_edge_score(
        overfit_probability=0.95,
        regime_sensitivity=2.0,
        mc_p_value=0.95,
        data_leakage_score=10.0,
        reconstruction_error=5.0,
    )
    assert result["edge_score"] <= 20


def test_sub_scores_present():
    result = compute_edge_score(
        overfit_probability=0.5,
        regime_sensitivity=0.5,
        mc_p_value=0.5,
        data_leakage_score=50.0,
        reconstruction_error=0.5,
    )
    expected_keys = [
        "edge_score", "overfit_sub_score", "regime_sub_score",
        "stat_sig_sub_score", "data_leakage_sub_score", "explainability_sub_score",
    ]
    for key in expected_keys:
        assert key in result


def test_data_leakage_score_bounds():
    # High risk scenario
    features = {
        "train_test_split_ratio": 0.95,
        "backtest_sharpe": 3.5,
        "num_parameters": 15,
        "sample_size": 20,
        "std_return": 0.001,
        "param_to_obs_ratio": 0.75,
    }
    score = compute_data_leakage_score(features)
    assert 0 <= score <= 100


def test_data_leakage_perfect():
    features = {
        "train_test_split_ratio": 0.65,
        "backtest_sharpe": 1.0,
        "num_parameters": 3,
        "sample_size": 120,
        "std_return": 0.03,
        "param_to_obs_ratio": 0.025,
    }
    score = compute_data_leakage_score(features)
    assert score == 100.0
