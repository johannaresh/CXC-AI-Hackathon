"""
Single-asset audit runner for EdgeAudit Phase 2.

Allows users to select a strategy and specific asset, then runs
a targeted audit on that selection. This demonstrates the new
user-driven flow for strategy/asset selection.
"""

import json
import logging
from pathlib import Path

try:
    import httpx
    USE_HTTPX = True
except ImportError:
    import requests
    USE_HTTPX = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "http://localhost:8000"
AUDIT_ENDPOINT = f"{BACKEND_URL}/audit"
STRATEGIES_ENDPOINT = f"{BACKEND_URL}/strategies/available"
STRATEGIES_FILE = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "synthetic_strategies.json"


def get_available_strategies():
    """Fetch available strategies from the API or local file."""
    # Try API first
    try:
        if USE_HTTPX:
            response = httpx.get(STRATEGIES_ENDPOINT, timeout=5.0)
        else:
            response = requests.get(STRATEGIES_ENDPOINT, timeout=5)
        
        response.raise_for_status()
        data = response.json()
        return data.get("strategies", [])
    except Exception as e:
        logger.warning(f"API call failed, loading from local file: {e}")
        
    # Fallback to local file
    if not STRATEGIES_FILE.exists():
        logger.error(f"Strategies file not found: {STRATEGIES_FILE}")
        return []
    
    try:
        with open(STRATEGIES_FILE, "r", encoding="utf-8") as f:
            strategies_data = json.load(f)
        
        return [
            {
                "name": strategy.get("name", ""),
                "assets": strategy.get("ticker_universe", [])
            }
            for strategy in strategies_data
        ]
    except Exception as e:
        logger.error(f"Failed to load strategies from file: {e}")
        return []


def select_strategy(strategies):
    """Let user select a strategy."""
    print("\n" + "=" * 70)
    print("AVAILABLE STRATEGIES")
    print("=" * 70)
    
    for idx, strategy in enumerate(strategies, 1):
        assets_str = ", ".join(strategy.get("assets", []))
        print(f"{idx}. {strategy['name']}")
        print(f"   Assets: {assets_str}")
    
    while True:
        try:
            choice = input("\nSelect a strategy (enter number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(strategies):
                return strategies[idx]
            print(f"Please enter a number between 1 and {len(strategies)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nAborted by user")
            return None


def select_asset(strategy):
    """Let user select an asset from the strategy's universe."""
    assets = strategy.get("assets", [])
    
    print("\n" + "=" * 70)
    print(f"ASSETS IN {strategy['name']}")
    print("=" * 70)
    
    for idx, asset in enumerate(assets, 1):
        print(f"{idx}. {asset}")
    
    while True:
        try:
            choice = input("\nSelect an asset (enter number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(assets):
                return assets[idx]
            print(f"Please enter a number between 1 and {len(assets)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nAborted by user")
            return None


def load_full_strategy(name):
    """Load full strategy data from the JSON file."""
    if not STRATEGIES_FILE.exists():
        logger.error(f"Strategies file not found: {STRATEGIES_FILE}")
        return None
    
    try:
        with open(STRATEGIES_FILE, "r", encoding="utf-8") as f:
            strategies = json.load(f)
        
        for strategy in strategies:
            if strategy.get("name") == name:
                return strategy
        
        logger.error(f"Strategy '{name}' not found in file")
        return None
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        return None


def run_audit(strategy_data, selected_asset):
    """Submit the audit request with selected_asset."""
    # Add selected_asset to the payload
    strategy_data["selected_asset"] = selected_asset
    
    print("\n" + "=" * 70)
    print("RUNNING AUDIT")
    print("=" * 70)
    print(f"Strategy: {strategy_data.get('name')}")
    print(f"Selected Asset: {selected_asset}")
    print(f"Submitting to: {AUDIT_ENDPOINT}")
    print("Please wait...")
    
    try:
        if USE_HTTPX:
            response = httpx.post(AUDIT_ENDPOINT, json=strategy_data, timeout=120.0)
        else:
            response = requests.post(AUDIT_ENDPOINT, json=strategy_data, timeout=120)
        
        response.raise_for_status()
        result = response.json()
        
        # Display results
        print("\n" + "=" * 70)
        print("AUDIT COMPLETE")
        print("=" * 70)
        
        audit_id = result.get("audit_id", "N/A")
        edge_score = result.get("edge_score", {}).get("edge_score", "N/A")
        overfit_prob = result.get("overfit_score", {}).get("probability", "N/A")
        narrative = result.get("narrative", "")
        
        print(f"\nAudit ID: {audit_id}")
        print(f"Edge Score: {edge_score}/100")
        print(f"Overfit Probability: {overfit_prob:.1%}" if isinstance(overfit_prob, (int, float)) else f"Overfit Probability: {overfit_prob}")
        print(f"\nNarrative:")
        print("-" * 70)
        print(narrative)
        print("\n" + "=" * 70)
        
        return True
        
    except (httpx.HTTPStatusError if USE_HTTPX else requests.HTTPError) as e:
        logger.error(f"HTTP ERROR: {e.response.status_code}")
        logger.error(f"Response: {e.response.text[:500]}")
        return False
        
    except (httpx.RequestError if USE_HTTPX else requests.RequestException) as e:
        logger.error(f"REQUEST ERROR: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")
        return False


def main():
    """Main function for single-asset audit selection and execution."""
    global BACKEND_URL, AUDIT_ENDPOINT, STRATEGIES_ENDPOINT
    
    print("\n" + "=" * 70)
    print("EDGEAUDIT - SINGLE STRATEGY/ASSET AUDIT")
    print("Phase 2: User-Driven Selection Flow")
    print("=" * 70)
    
    # Check if backend is running
    print(f"Connecting to backend at {BACKEND_URL}...")
    try:
        if USE_HTTPX:
            response = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        else:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        response.raise_for_status()
        print("\n✓ Backend is running")
    except Exception as e:
        # Try 127.0.0.1 fallback if localhost fails
        if "localhost" in BACKEND_URL:
            try:
                fallback_url = BACKEND_URL.replace("localhost", "127.0.0.1")
                print(f"Retrying with {fallback_url}...")
                if USE_HTTPX:
                    response = httpx.get(f"{fallback_url}/health", timeout=5.0)
                else:
                    response = requests.get(f"{fallback_url}/health", timeout=5)
                response.raise_for_status()
                
                # Update globals to use fallback URL
                BACKEND_URL = fallback_url
                AUDIT_ENDPOINT = f"{BACKEND_URL}/audit"
                STRATEGIES_ENDPOINT = f"{BACKEND_URL}/strategies/available"
                print("\n✓ Backend is running (using 127.0.0.1)")
            except Exception:
                pass

        print("\n✗ Backend is not responding!")
        print(f"Error: {e}")
        print(f"Please start the backend first:")
        print(f"  cd C:\\Users\\ryous\\Downloads\\edgeauditcxc\\CXC-AI-Hackathon\\edgeaudit")
        print(f"  uvicorn backend.app.main:app --reload")
        return
    
    # Get available strategies
    strategies = get_available_strategies()
    if not strategies:
        logger.error("No strategies available")
        return
    
    # Let user select strategy
    selected_strategy = select_strategy(strategies)
    if not selected_strategy:
        return
    
    # Let user select asset
    selected_asset = select_asset(selected_strategy)
    if not selected_asset:
        return
    
    # Load full strategy data
    full_strategy = load_full_strategy(selected_strategy["name"])
    if not full_strategy:
        logger.error(f"Could not load full data for {selected_strategy['name']}")
        return
    
    # Run the audit
    success = run_audit(full_strategy, selected_asset)
    
    if success:
        print("\n✓ Audit completed successfully!")
        print(f"\nNext steps:")
        print(f"  - View this audit in Backboard.io dashboard")
        print(f"  - Check Snowflake AUDIT_RESULTS table for SELECTED_ASSET column")
    else:
        print("\n✗ Audit failed. Check logs above for details.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user")
