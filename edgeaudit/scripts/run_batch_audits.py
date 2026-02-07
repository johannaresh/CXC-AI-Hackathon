"""
Batch audit runner for EdgeAudit.

Loads synthetic strategies from data/synthetic/synthetic_strategies.json
and submits each one to the local backend /audit endpoint.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

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
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
STRATEGIES_FILE = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "synthetic_strategies.json"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds


def check_backend_health() -> dict:
    """Check backend health and configuration status."""
    try:
        if USE_HTTPX:
            response = httpx.get(HEALTH_ENDPOINT, timeout=5.0)
        else:
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to check backend health: {e}")
        return {}


def load_strategies() -> list[dict[str, Any]]:
    """Load strategies from the synthetic strategies JSON file."""
    if not STRATEGIES_FILE.exists():
        raise FileNotFoundError(f"Strategies file not found: {STRATEGIES_FILE}")
    
    with open(STRATEGIES_FILE, "r", encoding="utf-8") as f:
        strategies = json.load(f)
    
    logger.info(f"Loaded {len(strategies)} strategies from {STRATEGIES_FILE}")
    return strategies


def submit_strategy(strategy: dict[str, Any], client: Any = None) -> dict[str, Any] | None:
    """
    Submit a single strategy to the /audit endpoint.
    
    Args:
        strategy: Strategy payload matching StrategyPayload schema
        client: Optional HTTP client (httpx.Client or None for requests)
    
    Returns:
        Audit result dict if successful, None if failed
    """
    strategy_name = strategy.get("name", "Unknown")
    
    try:
        if USE_HTTPX and client:
            response = client.post(AUDIT_ENDPOINT, json=strategy, timeout=120.0)
        elif USE_HTTPX:
            response = httpx.post(AUDIT_ENDPOINT, json=strategy, timeout=120.0)
        else:
            response = requests.post(AUDIT_ENDPOINT, json=strategy, timeout=120)
        
        response.raise_for_status()
        result = response.json()
        
        # Extract key metrics for logging
        edge_score = result.get("edge_score", {}).get("edge_score", "N/A")
        overfit_prob = result.get("overfit_score", {}).get("probability", "N/A")
        
        logger.info(
            f"✓ SUCCESS: {strategy_name} | "
            f"Edge Score: {edge_score} | "
            f"Overfit Prob: {overfit_prob}"
        )
        return result
        
    except (httpx.HTTPStatusError if USE_HTTPX else requests.HTTPError) as e:
        logger.error(f"✗ HTTP ERROR: {strategy_name} | Status: {e.response.status_code}")
        logger.error(f"  Response: {e.response.text[:500]}")
        return None
        
    except (httpx.RequestError if USE_HTTPX else requests.RequestException) as e:
        logger.error(f"✗ REQUEST ERROR: {strategy_name} | {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {strategy_name} | {type(e).__name__}: {str(e)}")
        return None


def run_batch_audits(delay: float = DELAY_BETWEEN_REQUESTS, limit: int | None = None):
    """
    Run batch audits on all strategies.
    
    Args:
        delay: Delay in seconds between requests
        limit: Optional limit on number of strategies to process
    """
    logger.info("=" * 80)
    logger.info("Starting EdgeAudit Batch Audit Runner")
    logger.info("=" * 80)
    
    # Check backend health first
    logger.info("\n🔍 Checking backend health...")
    health = check_backend_health()
    
    if health:
        status = health.get("status", "unknown")
        snowflake_conn = health.get("snowflake_connected", False)
        gemini_conf = health.get("gemini_configured", False)
        
        logger.info(f"   Backend Status: {status}")
        logger.info(f"   Snowflake: {'✓ CONNECTED' if snowflake_conn else '✗ NOT CONNECTED'}")
        logger.info(f"   Gemini: {'✓ CONFIGURED' if gemini_conf else '✗ NOT CONFIGURED'}")
        
        if not snowflake_conn:
            logger.warning("\n⚠️  WARNING: Snowflake is not connected!")
            logger.warning("   Audit results will NOT be persisted to the database.")
            logger.warning("   To fix this:")
            logger.warning("   1. Check your .env file in the project root")
            logger.warning("   2. Ensure SNOWFLAKE_* variables are set correctly")
            logger.warning("   3. Restart the backend: uvicorn backend.app.main:app --reload")
            
            response = input("\n   Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                logger.info("Aborting batch audit.")
                return
        
        if not gemini_conf:
            logger.info("\n💡 NOTE: Gemini is not configured - using fallback narratives")
    else:
        logger.error("❌ Backend is not responding! Please start it first:")
        logger.error("   cd C:\\Users\\ryous\\Downloads\\edgeauditcxc\\CXC-AI-Hackathon\\edgeaudit")
        logger.error("   uvicorn backend.app.main:app --reload")
        return
    
    # Load strategies
    try:
        strategies = load_strategies()
    except FileNotFoundError as e:
        logger.error(f"Failed to load strategies: {e}")
        return
    
    if limit:
        strategies = strategies[:limit]
        logger.info(f"Limiting to first {limit} strategies")
    
    # Submit each strategy
    results = {
        "success": 0,
        "failed": 0,
        "total": len(strategies),
    }
    
    start_time = time.time()
    
    # Use persistent client if using httpx for better performance
    if USE_HTTPX:
        with httpx.Client() as client:
            for idx, strategy in enumerate(strategies, 1):
                logger.info(f"\n[{idx}/{len(strategies)}] Processing: {strategy.get('name', 'Unknown')}")
                
                result = submit_strategy(strategy, client=client)
                if result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                # Delay between requests (except for the last one)
                if idx < len(strategies) and delay > 0:
                    time.sleep(delay)
    else:
        for idx, strategy in enumerate(strategies, 1):
            logger.info(f"\n[{idx}/{len(strategies)}] Processing: {strategy.get('name', 'Unknown')}")
            
            result = submit_strategy(strategy)
            if result:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            # Delay between requests (except for the last one)
            if idx < len(strategies) and delay > 0:
                time.sleep(delay)
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("BATCH AUDIT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total Strategies: {results['total']}")
    logger.info(f"Successful: {results['success']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Elapsed Time: {elapsed_time:.2f}s")
    logger.info(f"Avg Time per Strategy: {elapsed_time / results['total']:.2f}s")
    logger.info("=" * 80)
    
    if results["success"] > 0:
        logger.info("\n🔍 To view results:")
        logger.info(f"   Leaderboard: curl -X GET {BACKEND_URL}/strategies/leaderboard")
        logger.info(f"   All strategies: curl -X GET {BACKEND_URL}/strategies")


if __name__ == "__main__":
    import sys
    
    # Optional: parse command line arguments
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            logger.info(f"Command line limit: {limit}")
        except ValueError:
            logger.warning(f"Invalid limit argument: {sys.argv[1]}, processing all strategies")
    
    run_batch_audits(limit=limit)
