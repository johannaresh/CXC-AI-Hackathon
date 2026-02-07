"""
Snowflake Client — handles connection and queries to Snowflake
for historical market data and strategy metadata.
"""

from backend.app.core.config import settings
from backend.app.core.logging import logger


def get_connection():
    """Create and return a Snowflake connection.

    TODO: Implement connection pooling.
    TODO: Add retry logic for transient failures.
    """
    logger.info("Connecting to Snowflake account=%s", settings.SNOWFLAKE_ACCOUNT)

    # --- Stub: uncomment when credentials are configured ---
    # import snowflake.connector
    # return snowflake.connector.connect(
    #     account=settings.SNOWFLAKE_ACCOUNT,
    #     user=settings.SNOWFLAKE_USER,
    #     password=settings.SNOWFLAKE_PASSWORD,
    #     warehouse=settings.SNOWFLAKE_WAREHOUSE,
    #     database=settings.SNOWFLAKE_DATABASE,
    #     schema=settings.SNOWFLAKE_SCHEMA,
    # )

    return None


def fetch_market_data(tickers: list[str], start_date: str, end_date: str) -> list[dict]:
    """Fetch historical market data from Snowflake.

    TODO: Implement actual SQL query against market data table.
    TODO: Return as a pandas DataFrame.

    Args:
        tickers: List of ticker symbols.
        start_date: ISO date string.
        end_date: ISO date string.

    Returns:
        List of row dicts (mock).
    """
    logger.info("Fetching market data for %s from %s to %s", tickers, start_date, end_date)
    return []
