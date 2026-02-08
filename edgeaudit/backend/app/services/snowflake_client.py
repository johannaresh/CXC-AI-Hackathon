"""
Snowflake Client — handles connection and queries to Snowflake
for historical market data, audit result persistence, and experiment tracking.
"""

import json
import uuid

from ..core.config import settings
from ..core.logging import logger

_connection = None


def _is_configured() -> bool:
    """Check if Snowflake credentials are configured."""
    return bool(settings.SNOWFLAKE_ACCOUNT and settings.SNOWFLAKE_USER)


def get_connection():
    """Create and return a Snowflake connection (cached at module level).

    Returns None if credentials are not configured.
    """
    global _connection

    if not _is_configured():
        return None

    if _connection is not None:
        try:
            _connection.cursor().execute("SELECT 1")
            return _connection
        except Exception:
            _connection = None

    try:
        import snowflake.connector
        logger.info("Connecting to Snowflake account=%s", settings.SNOWFLAKE_ACCOUNT)
        _connection = snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
        )
        return _connection
    except Exception as e:
        logger.error("Snowflake connection failed: %s", e)
        return None


def is_connected() -> bool:
    """Test if Snowflake is reachable."""
    conn = get_connection()
    return conn is not None


def store_audit_result(audit_result: dict, payload: dict) -> str:
    """Persist an audit result to Snowflake.

    Returns the audit_id (UUID) or empty string if Snowflake is unavailable.
    """
    conn = get_connection()
    if conn is None:
        logger.warning("Snowflake not connected — skipping audit persistence")
        return ""

    audit_id = str(uuid.uuid4())

    overfit = audit_result.get("overfit_score", {})
    regime = audit_result.get("regime_analysis", {})
    mc = audit_result.get("monte_carlo", {})
    edge = audit_result.get("edge_score", {})

    try:
        cursor = conn.cursor()
        
        # Convert Python objects to JSON strings for VARIANT columns
        payload_json = json.dumps(payload)
        recommendations_json = json.dumps(audit_result.get("recommendations", []))
        features_json = json.dumps(audit_result.get("features", {}))
        selected_asset = audit_result.get("selected_asset")
        
        cursor.execute(
            """
            INSERT INTO AUDIT_RESULTS (
                AUDIT_ID, STRATEGY_NAME, PAYLOAD_JSON,
                OVERFIT_PROBABILITY, OVERFIT_CONFIDENCE, OVERFIT_LABEL,
                REGIME_CURRENT, REGIME_SENSITIVITY,
                MC_SHARPE_MEAN, MC_SHARPE_STD, MC_P_VALUE, MC_NUM_SIMULATIONS,
                EDGE_SCORE, OVERFIT_SUB_SCORE, REGIME_SUB_SCORE,
                STAT_SIG_SUB_SCORE, DATA_LEAKAGE_SUB_SCORE, EXPLAIN_SUB_SCORE,
                NARRATIVE, RECOMMENDATIONS, FEATURE_VECTOR, SELECTED_ASSET
            )
            SELECT 
                %s, %s, PARSE_JSON(%s),
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, PARSE_JSON(%s), PARSE_JSON(%s), %s
            """,
            (
                audit_id,
                audit_result.get("strategy_name", ""),
                payload_json,
                overfit.get("probability", 0),
                overfit.get("confidence", 0),
                overfit.get("label", "medium"),
                regime.get("current_regime", ""),
                regime.get("regime_sensitivity", 0),
                mc.get("simulated_sharpe_mean", 0),
                mc.get("simulated_sharpe_std", 0),
                mc.get("p_value", 0),
                mc.get("num_simulations", 0),
                edge.get("edge_score", 0),
                edge.get("overfit_sub_score", 0),
                edge.get("regime_sub_score", 0),
                edge.get("stat_sig_sub_score", 0),
                edge.get("data_leakage_sub_score", 0),
                edge.get("explainability_sub_score", 0),
                audit_result.get("narrative", ""),
                recommendations_json,
                features_json,
                selected_asset,  # Store selected asset for targeted audits
            ),
        )
        logger.info("Stored audit result %s to Snowflake", audit_id)
        return audit_id
    except Exception as e:
        logger.error("Failed to store audit result: %s", e)
        return ""


def fetch_market_data(tickers: list[str], start_date: str, end_date: str) -> list[dict]:
    """Fetch historical market data from Snowflake."""
    conn = get_connection()
    if conn is None:
        return []

    try:
        import snowflake.connector
        placeholders = ", ".join(["%s"] * len(tickers))
        query = f"""
            SELECT TICKER, TRADE_DATE, ADJ_CLOSE, DAILY_RETURN
            FROM MARKET_DATA
            WHERE TICKER IN ({placeholders})
              AND TRADE_DATE BETWEEN %s AND %s
            ORDER BY TICKER, TRADE_DATE
        """
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(query, (*tickers, start_date, end_date))
        return cursor.fetchall()
    except Exception as e:
        logger.error("Failed to fetch market data: %s", e)
        return []


def get_audit_history(strategy_name: str, limit: int = 10) -> list[dict]:
    """Retrieve past audits for a strategy."""
    conn = get_connection()
    if conn is None:
        return []

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(
            """
            SELECT AUDIT_ID, SUBMITTED_AT, EDGE_SCORE,
                   OVERFIT_PROBABILITY, MC_P_VALUE, REGIME_SENSITIVITY
            FROM AUDIT_RESULTS
            WHERE STRATEGY_NAME = %s
            ORDER BY SUBMITTED_AT DESC
            LIMIT %s
            """,
            (strategy_name, limit),
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error("Failed to fetch audit history: %s", e)
        return []


def get_audit_by_id(audit_id: str) -> dict | None:
    """Retrieve a single audit result by ID."""
    conn = get_connection()
    if conn is None:
        return None

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(
            "SELECT * FROM AUDIT_RESULTS WHERE AUDIT_ID = %s",
            (audit_id,),
        )
        return cursor.fetchone()
    except Exception as e:
        logger.error("Failed to fetch audit by id: %s", e)
        return None


def get_leaderboard(limit: int = 20) -> list[dict]:
    """Top strategies by Edge Score (most recent audit per strategy)."""
    conn = get_connection()
    if conn is None:
        return []

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(
            """
            SELECT STRATEGY_NAME, EDGE_SCORE, OVERFIT_PROBABILITY,
                   MC_P_VALUE, SUBMITTED_AT
            FROM AUDIT_RESULTS
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY STRATEGY_NAME ORDER BY SUBMITTED_AT DESC
            ) = 1
            ORDER BY EDGE_SCORE DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error("Failed to fetch leaderboard: %s", e)
        return []


def get_all_strategies() -> list[dict]:
    """List all audited strategies with latest scores."""
    conn = get_connection()
    if conn is None:
        return []

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)
        cursor.execute(
            """
            SELECT STRATEGY_NAME,
                   MAX(EDGE_SCORE) AS LATEST_EDGE_SCORE,
                   MAX(SUBMITTED_AT) AS LAST_AUDITED,
                   COUNT(*) AS AUDIT_COUNT
            FROM AUDIT_RESULTS
            GROUP BY STRATEGY_NAME
            ORDER BY LAST_AUDITED DESC
            """
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error("Failed to fetch strategies: %s", e)
        return []
