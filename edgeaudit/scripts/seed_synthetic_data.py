"""
Seed Synthetic Data — generates mock strategy datasets
for local development and testing.

Usage:
    python -m scripts.seed_synthetic_data
"""

import json
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "synthetic"


def generate_strategy(name: str) -> dict:
    n_returns = random.randint(24, 120)
    raw_returns = [round(random.gauss(0.005, 0.03), 6) for _ in range(n_returns)]
    return {
        "name": name,
        "description": f"Synthetic strategy: {name}",
        "ticker_universe": random.sample(
            ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA", "JPM"], k=3
        ),
        "backtest_sharpe": round(random.uniform(0.5, 3.0), 2),
        "backtest_max_drawdown": round(random.uniform(-0.40, -0.05), 3),
        "backtest_start_date": "2018-01-01",
        "backtest_end_date": "2023-12-31",
        "num_parameters": random.randint(2, 20),
        "train_test_split_ratio": round(random.uniform(0.5, 0.8), 2),
        "rebalance_frequency": random.choice(["daily", "weekly", "monthly"]),
        "raw_returns": raw_returns,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    strategies = [generate_strategy(f"SyntheticStrategy_{i}") for i in range(20)]
    output_path = OUTPUT_DIR / "synthetic_strategies.json"
    output_path.write_text(json.dumps(strategies, indent=2))
    print(f"Generated {len(strategies)} synthetic strategies → {output_path}")


if __name__ == "__main__":
    main()
