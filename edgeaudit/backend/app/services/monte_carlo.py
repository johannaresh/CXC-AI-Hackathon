"""
Monte Carlo Simulation — bootstraps strategy returns to test
whether observed Sharpe ratios are statistically significant.
"""

import numpy as np


def run_simulation(
    raw_returns: list[float],
    observed_sharpe: float,
    num_simulations: int = 10000,
) -> dict:
    """Run Monte Carlo simulation on strategy returns.

    TODO: Implement bootstrap resampling of returns.
    TODO: Compute distribution of simulated Sharpe ratios.
    TODO: Calculate p-value for observed Sharpe vs null distribution.
    TODO: Replace mock with real simulation.

    Args:
        raw_returns: List of periodic strategy returns.
        observed_sharpe: The reported backtest Sharpe ratio.
        num_simulations: Number of bootstrap iterations.

    Returns:
        Dict with simulated_sharpe_mean, simulated_sharpe_std,
        p_value, and num_simulations.
    """
    # --- Mock implementation ---
    return {
        "simulated_sharpe_mean": 0.45,
        "simulated_sharpe_std": 0.38,
        "p_value": 0.12,
        "num_simulations": num_simulations,
    }
