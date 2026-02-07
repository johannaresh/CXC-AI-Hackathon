"""
Monte Carlo Simulation — circular block bootstrap of strategy returns
to test whether observed Sharpe ratios are statistically significant.
"""

import numpy as np
from scipy import stats


def run_simulation(
    raw_returns: list[float],
    observed_sharpe: float,
    num_simulations: int = 10_000,
    block_size: int = 5,
) -> dict:
    """Run circular block bootstrap simulation on strategy returns.

    Preserves autocorrelation structure by resampling contiguous blocks
    rather than individual observations.

    Args:
        raw_returns: List of periodic strategy returns.
        observed_sharpe: The reported backtest Sharpe ratio.
        num_simulations: Number of bootstrap iterations.
        block_size: Size of each resampled block.

    Returns:
        Dict with simulated stats, p-value, confidence interval, and percentile.
    """
    returns = np.array(raw_returns, dtype=np.float64)
    n = len(returns)

    if n < 10:
        return {
            "simulated_sharpe_mean": 0.0,
            "simulated_sharpe_std": 0.0,
            "p_value": 1.0,
            "num_simulations": 0,
            "confidence_interval_95": [0.0, 0.0],
            "sharpe_percentile": 0.0,
        }

    # Annualization factor: assume monthly if not specified
    ann_factor = np.sqrt(12)

    num_blocks = int(np.ceil(n / block_size))
    simulated_sharpes = np.empty(num_simulations)

    for i in range(num_simulations):
        # Random block start indices (circular)
        block_starts = np.random.randint(0, n, size=num_blocks)

        # Assemble bootstrapped return series
        blocks = []
        for start in block_starts:
            if start + block_size <= n:
                blocks.append(returns[start:start + block_size])
            else:
                # Circular wrap
                blocks.append(np.concatenate([
                    returns[start:],
                    returns[:(start + block_size) - n],
                ]))
        boot_returns = np.concatenate(blocks)[:n]

        # Compute Sharpe of bootstrapped series
        std_r = np.std(boot_returns, ddof=1)
        if std_r > 1e-10:
            simulated_sharpes[i] = np.mean(boot_returns) / std_r * ann_factor
        else:
            simulated_sharpes[i] = 0.0

    # P-value: fraction of simulations that exceed observed Sharpe
    p_value = float(np.mean(simulated_sharpes >= observed_sharpe))

    # 95% confidence interval of simulated Sharpe distribution
    ci_lower = float(np.percentile(simulated_sharpes, 2.5))
    ci_upper = float(np.percentile(simulated_sharpes, 97.5))

    # Where the observed Sharpe falls in the distribution
    sharpe_percentile = float(stats.percentileofscore(simulated_sharpes, observed_sharpe))

    return {
        "simulated_sharpe_mean": round(float(np.mean(simulated_sharpes)), 4),
        "simulated_sharpe_std": round(float(np.std(simulated_sharpes)), 4),
        "p_value": round(p_value, 4),
        "num_simulations": num_simulations,
        "confidence_interval_95": [round(ci_lower, 4), round(ci_upper, 4)],
        "sharpe_percentile": round(sharpe_percentile, 2),
    }
