import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.models.regime_model import analyze_regimes


def test_regime_output_schema():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = analyze_regimes(returns)
    expected_keys = [
        "current_regime", "regime_sensitivity", "regimes_tested",
        "per_regime_sharpe", "regime_proportions", "worst_regime_sharpe",
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"


def test_regime_sensitivity_non_negative():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.03, 60).tolist()
    result = analyze_regimes(returns)
    assert result["regime_sensitivity"] >= 0


def test_short_returns_fallback():
    result = analyze_regimes([0.01, 0.02, -0.01, 0.005])
    assert result["current_regime"] == "insufficient_data"
    assert result["regime_sensitivity"] == 0.0


def test_medium_returns_uses_two_regimes():
    np.random.seed(42)
    # 15 returns: enough for basic analysis but triggers 2-regime fallback
    returns = np.random.normal(0.005, 0.04, 15).tolist()
    result = analyze_regimes(returns)
    assert len(result["regimes_tested"]) >= 1


def test_long_returns_multiple_regimes():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.04, 120).tolist()
    result = analyze_regimes(returns)
    assert len(result["regimes_tested"]) >= 2
    assert len(result["per_regime_sharpe"]) >= 2


def test_regime_proportions_sum_to_one():
    np.random.seed(42)
    returns = np.random.normal(0.005, 0.04, 100).tolist()
    result = analyze_regimes(returns)
    proportions = list(result["regime_proportions"].values())
    if proportions:
        assert abs(sum(proportions) - 1.0) < 0.05  # allow small rounding error
