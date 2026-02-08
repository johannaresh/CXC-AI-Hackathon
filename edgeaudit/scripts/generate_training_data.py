"""
Generate Synthetic Training Data — creates 3,000 labeled strategies
across clean / overfit / p-hacked categories for ML model training.

Usage:
    python -m scripts.generate_training_data
"""

import json
import random
import math
from pathlib import Path
import pandas as pd
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "synthetic"

TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA", "JPM",
           "BAC", "V", "MA", "UNH", "HD", "PG", "JNJ", "XOM", "SPY", "QQQ"]


def _sharpe(returns: np.ndarray) -> float:
    if len(returns) < 2:
        return 0.0
    std = np.std(returns, ddof=1)
    if std < 1e-10:
        return 0.0
    return float(np.mean(returns) / std * np.sqrt(12))  # annualized monthly


def _max_drawdown(returns: np.ndarray) -> float:
    cumulative = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak
    return float(np.min(drawdown)) if len(drawdown) > 0 else 0.0


# ---------------------------------------------------------------------------
# Category 1: Clean strategies (genuine edge, not overfit)
# ---------------------------------------------------------------------------
def generate_clean_strategy(idx: int) -> dict:
    """Stable GBM returns with genuine positive drift."""
    n_periods = random.randint(60, 120)
    drift = random.uniform(0.003, 0.01)  # monthly drift
    vol = random.uniform(0.02, 0.06)
    returns = np.random.normal(drift, vol, n_periods)

    num_params = random.randint(2, 5)
    split_ratio = random.uniform(0.55, 0.72)

    raw = returns.tolist()
    sharpe = _sharpe(returns)
    mdd = _max_drawdown(returns)

    return {
        "name": f"CleanStrategy_{idx}",
        "description": f"Synthetic clean strategy #{idx}",
        "ticker_universe": random.sample(TICKERS, k=random.randint(2, 5)),
        "backtest_sharpe": round(sharpe, 3),
        "backtest_max_drawdown": round(mdd, 4),
        "backtest_start_date": "2015-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": num_params,
        "train_test_split_ratio": round(split_ratio, 2),
        "rebalance_frequency": random.choice(["daily", "weekly", "monthly"]),
        "raw_returns": [round(r, 6) for r in raw], # type: ignore
        # Labels
        "is_overfit": False,
        "overfit_severity": round(random.uniform(0.0, 0.15), 3),
        "generation_method": "synthetic_clean",
    }


# ---------------------------------------------------------------------------
# Category 2: Overfit strategies (noise with cherry-picked windows)
# ---------------------------------------------------------------------------
def generate_overfit_strategy(idx: int) -> dict:
    """Noise-based returns with parameter bloat and cherry-picked periods."""
    # Generate a long noisy series, pick the best-looking window
    full_length = random.randint(200, 400)
    noise = np.random.normal(0.0, random.uniform(0.03, 0.07), full_length)

    # Cherry-pick: slide a window and pick the one with highest Sharpe
    window_size = random.randint(30, 60)
    best_sharpe = -999
    best_start = 0
    for start in range(0, full_length - window_size, 5):
        seg = noise[start:start + window_size]
        s = _sharpe(seg)
        if s > best_sharpe:
            best_sharpe = s
            best_start = start

    returns = noise[best_start:best_start + window_size]

    # High parameter count relative to sample
    num_params = random.randint(8, 20)
    split_ratio = random.uniform(0.78, 0.95)

    raw = returns.tolist()
    sharpe = _sharpe(returns)
    mdd = _max_drawdown(returns)

    # Compute severity
    param_obs_ratio = num_params / len(returns)
    severity = min(1.0, 0.3 + param_obs_ratio * 3 + (split_ratio - 0.7) * 2)

    return {
        "name": f"OverfitStrategy_{idx}",
        "description": f"Synthetic overfit strategy #{idx}",
        "ticker_universe": random.sample(TICKERS, k=random.randint(3, 8)),
        "backtest_sharpe": round(sharpe, 3),
        "backtest_max_drawdown": round(mdd, 4),
        "backtest_start_date": "2018-01-01",
        "backtest_end_date": "2023-06-30",
        "num_parameters": num_params,
        "train_test_split_ratio": round(split_ratio, 2),
        "rebalance_frequency": random.choice(["daily", "weekly", "monthly"]),
        "raw_returns": [round(r, 6) for r in raw], # type: ignore
        # Labels
        "is_overfit": True,
        "overfit_severity": round(min(severity, 1.0), 3),
        "generation_method": "synthetic_overfit",
    }


# ---------------------------------------------------------------------------
# Category 3: P-hacked strategies (best-of-N selection)
# ---------------------------------------------------------------------------
def generate_phacked_strategy(idx: int) -> dict:
    """Run many random strategies, select the one with the best Sharpe."""
    n_periods = random.randint(36, 80)
    num_trials = random.randint(50, 200)
    vol = random.uniform(0.03, 0.06)

    best_sharpe = -999
    best_returns = None

    for _ in range(num_trials):
        trial = np.random.normal(0.0, vol, n_periods)  # zero drift = no real edge
        s = _sharpe(trial)
        if s > best_sharpe:
            best_sharpe = s
            best_returns = trial

    assert best_returns is not None, "No trials were run"
    returns = best_returns

    num_params = random.randint(5, 15)
    split_ratio = random.uniform(0.65, 0.90)

    raw = returns.tolist()
    sharpe = _sharpe(returns)
    mdd = _max_drawdown(returns)

    # P-hacked severity depends on number of trials
    selection_severity = min(num_trials / 200, 0.5)
    param_severity = min(num_params / len(returns) * 3, 0.3)
    severity = 0.4 + selection_severity + param_severity

    return {
        "name": f"PHackedStrategy_{idx}",
        "description": f"Synthetic p-hacked strategy #{idx}",
        "ticker_universe": random.sample(TICKERS, k=random.randint(3, 10)),
        "backtest_sharpe": round(sharpe, 3),
        "backtest_max_drawdown": round(mdd, 4),
        "backtest_start_date": "2019-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": num_params,
        "train_test_split_ratio": round(split_ratio, 2),
        "rebalance_frequency": random.choice(["daily", "weekly", "monthly"]),
        "raw_returns": [round(r, 6) for r in raw], # type: ignore
        # Labels
        "is_overfit": True,
        "overfit_severity": round(min(severity, 1.0), 3),
        "generation_method": "synthetic_phacked",
        "selection_count": num_trials,
    }


def main():
    random.seed(42)
    np.random.seed(42)

    strategies = []

    print("Generating 1,000 clean strategies...")
    for i in range(1000):
        strategies.append(generate_clean_strategy(i))

    print("Generating 1,000 overfit strategies...")
    for i in range(1000):
        strategies.append(generate_overfit_strategy(i))

    print("Generating 1,000 p-hacked strategies...")
    for i in range(1000):
        strategies.append(generate_phacked_strategy(i))

    # Shuffle
    random.shuffle(strategies)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "training_strategies.json"
    output_path.write_text(json.dumps(strategies, indent=2))

    # Print summary
    clean = sum(1 for s in strategies if not s["is_overfit"])
    overfit = sum(1 for s in strategies if s["is_overfit"])
    print(f"\nGenerated {len(strategies)} strategies -> {output_path}")
    print(f"  Clean: {clean}, Overfit/P-hacked: {overfit}")
    print(f"  Avg severity (overfit only): {np.mean([s['overfit_severity'] for s in strategies if s['is_overfit']]):.3f}")


if __name__ == "__main__":
    main()
