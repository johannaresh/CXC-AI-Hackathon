from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
        "raw_returns": [0.01, -0.005, 0.02, 0.015, -0.01, 0.008],
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
    assert response.json()["strategy_name"] == "MinimalStrategy"
