import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.services.monte_carlo import run_simulation


def test_simulation_output_schema():
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = run_simulation(returns, observed_sharpe=1.5, num_simulations=1000)
    expected_keys = [
        "simulated_sharpe_mean", "simulated_sharpe_std", "p_value",
        "num_simulations", "confidence_interval_95", "sharpe_percentile",
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"


def test_p_value_bounds():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = run_simulation(returns, observed_sharpe=1.5, num_simulations=1000)
    assert 0.0 <= result["p_value"] <= 1.0


def test_confidence_interval_ordered():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = run_simulation(returns, observed_sharpe=1.5, num_simulations=1000)
    ci = result["confidence_interval_95"]
    assert len(ci) == 2
    assert ci[0] <= ci[1]


def test_empty_returns_graceful():
    result = run_simulation([], observed_sharpe=1.0)
    assert result["p_value"] == 1.0
    assert result["num_simulations"] == 0


def test_short_returns_graceful():
    result = run_simulation([0.01, 0.02, 0.03], observed_sharpe=1.0)
    assert result["p_value"] == 1.0
    assert result["num_simulations"] == 0


def test_sharpe_percentile_range():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = run_simulation(returns, observed_sharpe=1.0, num_simulations=1000)
    assert 0.0 <= result["sharpe_percentile"] <= 100.0
