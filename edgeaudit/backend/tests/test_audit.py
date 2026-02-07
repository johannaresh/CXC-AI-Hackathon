import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "snowflake_connected" in data
    assert "gemini_configured" in data


def test_audit_returns_valid_result():
    payload = {
        "name": "MomentumAlpha",
        "description": "Simple momentum strategy",
        "ticker_universe": ["AAPL", "MSFT"],
        "backtest_sharpe": 1.8,
        "backtest_max_drawdown": -0.15,
        "backtest_start_date": "2018-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": 5,
        "train_test_split_ratio": 0.7,
        "rebalance_frequency": "monthly",
        "raw_returns": [0.01, -0.005, 0.02, 0.015, -0.01, 0.008,
                        0.003, -0.012, 0.018, 0.007, -0.003, 0.011,
                        0.005, -0.008, 0.014, 0.002, -0.006, 0.009,
                        0.012, -0.004, 0.016, 0.001, -0.007, 0.013],
    }
    response = client.post("/audit", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["strategy_name"] == "MomentumAlpha"
    assert "overfit_score" in data
    assert "regime_analysis" in data
    assert "monte_carlo" in data
    assert "narrative" in data
    assert isinstance(data["recommendations"], list)

    # Edge score present
    assert "edge_score" in data
    assert data["edge_score"] is not None
    score = data["edge_score"]["edge_score"]
    assert 0 <= score <= 100

    # Regime expanded fields
    regime = data["regime_analysis"]
    assert "per_regime_sharpe" in regime
    assert "regime_proportions" in regime

    # Monte Carlo expanded fields
    mc = data["monte_carlo"]
    assert "confidence_interval_95" in mc
    assert "sharpe_percentile" in mc


def test_audit_minimal_payload():
    payload = {
        "name": "MinimalStrategy",
        "backtest_sharpe": 1.0,
        "backtest_max_drawdown": -0.10,
        "backtest_start_date": "2020-01-01",
        "backtest_end_date": "2023-01-01",
        "num_parameters": 3,
    }
    response = client.post("/audit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_name"] == "MinimalStrategy"
    assert data["edge_score"] is not None
