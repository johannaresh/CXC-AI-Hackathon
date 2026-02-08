"""Test script for the new GET /audit/{audit_id} endpoint."""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_submit_audit():
    """Submit a test audit and get the audit_id."""
    print("Submitting test audit...")

    # Load a sample strategy from training data
    test_strategy = {
        "name": "TestStrategy_BackboardIntegration",
        "description": "Test strategy for Backboard integration",
        "ticker_universe": ["SPY", "QQQ"],
        "backtest_sharpe": 1.65,
        "backtest_max_drawdown": -0.12,
        "backtest_start_date": "2019-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": 8,
        "train_test_split_ratio": 0.75,
        "rebalance_frequency": "monthly",
        "raw_returns": [
            0.054, -0.086, 0.197, -0.043, 0.132, 0.076, -0.021, 0.165,
            -0.092, 0.203, 0.045, -0.134, 0.187, 0.023, -0.056, 0.112,
            0.089, -0.145, 0.234, 0.011, -0.098, 0.156, 0.034, -0.067,
            0.198, -0.023, 0.087, 0.145, -0.112, 0.176, 0.056, -0.134,
            0.209, 0.034, -0.087, 0.123, 0.067, -0.156, 0.189, 0.012,
            -0.098, 0.134, 0.078, -0.045, 0.167, 0.089, -0.123, 0.201
        ],
        "selected_asset": "SPY"
    }

    response = requests.post(f"{BASE_URL}/audit", json=test_strategy)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        audit_id = result.get("audit_id")
        edge_score = result.get("edge_score", {}).get("edge_score")
        print(f"✅ Audit submitted successfully!")
        print(f"Audit ID: {audit_id}")
        print(f"Edge Score: {edge_score}")
        print()
        return audit_id
    else:
        print(f"❌ Failed to submit audit: {response.text}")
        print()
        return None

def test_get_audit(audit_id):
    """Test the new GET /audit/{audit_id} endpoint."""
    print(f"Testing GET /audit/{audit_id}...")

    response = requests.get(f"{BASE_URL}/audit/{audit_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Retrieved audit successfully!")
        print(f"\nAudit Details:")
        print(f"  Strategy: {result.get('strategy_name')}")
        print(f"  Edge Score: {result.get('edge_score', {}).get('edge_score')}")
        print(f"  Overfit Probability: {result.get('overfit_score', {}).get('probability')}")
        print(f"  Overfit Label: {result.get('overfit_score', {}).get('label')}")
        print(f"  Monte Carlo P-value: {result.get('monte_carlo', {}).get('p_value')}")
        print(f"  Current Regime: {result.get('regime_analysis', {}).get('current_regime')}")
        print(f"  Narrative length: {len(result.get('narrative', ''))} characters")
        print(f"  Recommendations count: {len(result.get('recommendations', []))}")
        print()
        print("Full response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Failed to retrieve audit: {response.text}")
    print()

def test_404():
    """Test that non-existent audit returns 404."""
    print("Testing 404 for non-existent audit...")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{BASE_URL}/audit/{fake_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print(f"✅ Correctly returns 404 for non-existent audit")
    else:
        print(f"❌ Expected 404, got {response.status_code}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("EdgeAudit API Endpoint Tests")
    print("=" * 60)
    print()

    print("Make sure the backend server is running:")
    print("  cd edgeaudit")
    print("  uvicorn backend.app.main:app --reload")
    print()
    input("Press Enter when server is ready...")
    print()

    # Test sequence
    test_health()

    # Submit audit and get ID
    audit_id = test_submit_audit()

    if audit_id:
        # Test retrieving the audit
        test_get_audit(audit_id)

    # Test 404
    test_404()

    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)
