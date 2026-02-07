from pydantic import BaseModel


class StrategyPayload(BaseModel):
    """Incoming strategy submission for auditing."""

    name: str
    description: str | None = None
    ticker_universe: list[str] = []
    backtest_sharpe: float
    backtest_max_drawdown: float
    backtest_start_date: str
    backtest_end_date: str
    num_parameters: int
    train_test_split_ratio: float = 0.7
    rebalance_frequency: str = "monthly"
    raw_returns: list[float] = []
