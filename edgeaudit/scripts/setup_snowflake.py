"""
Setup Snowflake — creates all required tables for EdgeAudit.

Usage:
    python -m scripts.setup_snowflake
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.snowflake_client import get_connection
from backend.app.core.logging import logger

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS MARKET_DATA (
        TICKER        VARCHAR(10)    NOT NULL,
        TRADE_DATE    DATE           NOT NULL,
        OPEN_PRICE    FLOAT,
        HIGH_PRICE    FLOAT,
        LOW_PRICE     FLOAT,
        CLOSE_PRICE   FLOAT          NOT NULL,
        ADJ_CLOSE     FLOAT          NOT NULL,
        VOLUME        BIGINT,
        DAILY_RETURN  FLOAT,
        INGESTED_AT   TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
        PRIMARY KEY (TICKER, TRADE_DATE)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS AUDIT_RESULTS (
        AUDIT_ID               VARCHAR(36)    PRIMARY KEY,
        STRATEGY_NAME          VARCHAR(255)   NOT NULL,
        SUBMITTED_AT           TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
        PAYLOAD_JSON           VARIANT,
        OVERFIT_PROBABILITY    FLOAT,
        OVERFIT_CONFIDENCE     FLOAT,
        OVERFIT_LABEL          VARCHAR(10),
        REGIME_CURRENT         VARCHAR(50),
        REGIME_SENSITIVITY     FLOAT,
        MC_SHARPE_MEAN         FLOAT,
        MC_SHARPE_STD          FLOAT,
        MC_P_VALUE             FLOAT,
        MC_NUM_SIMULATIONS     INT,
        EDGE_SCORE             FLOAT,
        OVERFIT_SUB_SCORE      FLOAT,
        REGIME_SUB_SCORE       FLOAT,
        STAT_SIG_SUB_SCORE     FLOAT,
        DATA_LEAKAGE_SUB_SCORE FLOAT,
        EXPLAIN_SUB_SCORE      FLOAT,
        NARRATIVE              VARCHAR(10000),
        RECOMMENDATIONS        VARIANT,
        FEATURE_VECTOR         VARIANT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS STRATEGY_EXPERIMENTS (
        EXPERIMENT_ID    VARCHAR(36)    PRIMARY KEY,
        STRATEGY_NAME    VARCHAR(255),
        VERSION          INT            DEFAULT 1,
        AUDIT_ID         VARCHAR(36),
        PARENT_AUDIT_ID  VARCHAR(36),
        CREATED_AT       TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP(),
        NOTES            VARCHAR(2000)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS TRAINING_DATA (
        SAMPLE_ID          VARCHAR(36)    PRIMARY KEY,
        FEATURE_VECTOR     VARIANT,
        IS_OVERFIT         BOOLEAN,
        OVERFIT_SEVERITY   FLOAT,
        GENERATION_METHOD  VARCHAR(50),
        CREATED_AT         TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
    )
    """,
]


def main():
    conn = get_connection()
    if conn is None:
        print("ERROR: Could not connect to Snowflake. Check your .env credentials.")
        sys.exit(1)

    cursor = conn.cursor()
    for i, ddl in enumerate(DDL_STATEMENTS):
        table_name = ddl.split("IF NOT EXISTS")[1].split("(")[0].strip()
        print(f"Creating table {table_name}...")
        cursor.execute(ddl)
        print(f"  -> OK")

    print("\nAll tables created successfully.")


if __name__ == "__main__":
    main()
