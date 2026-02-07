"""
Seed Snowflake MARKET_DATA table with real market data from Yahoo Finance.

This script fetches historical OHLCV data for major tickers and inserts
them into the MARKET_DATA table in Snowflake.

Usage:
    python -m scripts.seed_market_data
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

# Major tickers to seed
TICKERS = [
    # US Large Cap
    "SPY",   # S&P 500 ETF
    "QQQ",   # Nasdaq 100 ETF
    "IWM",   # Russell 2000 ETF
    "DIA",   # Dow Jones ETF
    # Tech
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    # Financials
    "JPM",
    "BAC",
    "GS",
    # Energy
    "XOM",
    "CVX",
    # Commodities
    "GLD",   # Gold ETF
    "USO",   # Oil ETF
    # Bonds
    "TLT",   # 20+ Year Treasury ETF
    "IEF",   # 7-10 Year Treasury ETF
    # Volatility
    "VXX",   # VIX Short-Term Futures
    # International
    "EEM",   # Emerging Markets ETF
    "EFA",   # Developed Markets ETF
]

# Date range: last 5 years
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=7 * 365)


def get_snowflake_connection():
    """Get Snowflake connection."""
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
        user=os.getenv("SNOWFLAKE_USER", ""),
        password=os.getenv("SNOWFLAKE_PASSWORD", ""),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "EDGEAUDIT_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    )
    return conn


def fetch_ticker_data(ticker: str) -> list[dict]:
    """Fetch OHLCV data for a single ticker."""
    print(f"  Fetching {ticker}...")
    try:
        data = yf.download(
            ticker,
            start=START_DATE.strftime("%Y-%m-%d"),
            end=END_DATE.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=False,
        )

        # yf.download can return None in edge cases
        if data is None:
            print(f"    No data for {ticker}")
            return []

        import pandas as pd

        if not isinstance(data, pd.DataFrame):
            print(f"    Unexpected return type for {ticker}: {type(data)}")
            return []

        # yfinance >= 0.2.31 returns MultiIndex columns like (Price, Ticker).
        # Flatten them so we get simple column names: Open, High, Low, etc.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel("Ticker")

        if data.shape[0] == 0:
            print(f"    No data for {ticker}")
            return []

        # Normalize column names for consistent access
        data.columns = pd.Index([str(c).strip() for c in data.columns])

        # Strip timezone from DatetimeIndex so .strftime works reliably
        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        records: list[dict] = []
        for date_idx, row in data.iterrows():
            try:
                # Convert the index timestamp to a plain date string
                if isinstance(date_idx, pd.Timestamp):
                    trade_date = date_idx.strftime("%Y-%m-%d")
                else:
                    trade_date = str(date_idx)

                open_price = float(row.get("Open", 0.0))
                high_price = float(row.get("High", 0.0))
                low_price = float(row.get("Low", 0.0))
                close_price = float(row.get("Close", 0.0))
                adj_close = float(row.get("Adj Close", close_price))
                volume = int(row.get("Volume", 0))

                # Skip rows where close is NaN (e.g. holidays)
                if close_price != close_price:  # NaN check
                    continue

                records.append({
                    "ticker": ticker,
                    "date": trade_date,
                    "open": open_price if open_price == open_price else 0.0,
                    "high": high_price if high_price == high_price else 0.0,
                    "low": low_price if low_price == low_price else 0.0,
                    "close": close_price,
                    "adj_close": adj_close if adj_close == adj_close else close_price,
                    "volume": volume if volume == volume else 0,
                })
            except Exception as row_err:
                print(f"    Skipping row due to error: {row_err}")
                continue
        print(f"    Fetched {len(records)} rows for {ticker}")
        return records
    except Exception as e:
        print(f"    Error fetching {ticker}: {e}")
        return []


def insert_records(conn, records: list[dict]) -> int:
    """Insert records into MARKET_DATA table."""
    if not records:
        return 0

    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO MARKET_DATA (TICKER, TRADE_DATE, OPEN_PRICE, HIGH_PRICE, 
                                  LOW_PRICE, CLOSE_PRICE, ADJ_CLOSE, VOLUME)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    batch = []
    for rec in records:
        batch.append((
            rec["ticker"],
            rec["date"],
            rec["open"],
            rec["high"],
            rec["low"],
            rec["close"],
            rec["adj_close"],
            rec["volume"],
        ))

    try:
        cursor.executemany(insert_sql, batch)
        conn.commit()
        return len(batch)
    except Exception as e:
        print(f"    Insert error: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()


def clear_existing_data(conn):
    """Clear existing market data (optional fresh start)."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM MARKET_DATA")
        conn.commit()
        print("Cleared existing market data.")
    except Exception as e:
        print(f"Could not clear existing data: {e}")
        conn.rollback()
    finally:
        cursor.close()


def main():
    print("=" * 60)
    print("EdgeAudit Market Data Seeder")
    print("=" * 60)
    print(f"Tickers: {len(TICKERS)}")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()

    # Connect to Snowflake
    print("Connecting to Snowflake...")
    try:
        conn = get_snowflake_connection()
        clear_existing_data(conn)
        print("Connected successfully!")
    except Exception as e:
        print(f"Failed to connect to Snowflake: {e}")
        print("Check your SNOWFLAKE_* environment variables.")
        sys.exit(1)

    # Optional: Clear existing data for fresh seed
    # clear_existing_data(conn)

    # Fetch and insert data for each ticker
    total_inserted = 0
    print("\nFetching market data...")
    for ticker in TICKERS:
        records = fetch_ticker_data(ticker)
        if records:
            inserted = insert_records(conn, records)
            total_inserted += inserted

    print()
    print("=" * 60)
    print(f"Seeding complete! Inserted {total_inserted} total records.")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
