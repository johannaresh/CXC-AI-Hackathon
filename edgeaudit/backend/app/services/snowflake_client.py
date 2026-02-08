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
    configured = bool(settings.SNOWFLAKE_ACCOUNT and settings.SNOWFLAKE_USER)
    if not configured:
        logger.warning("Snowflake not configured: ACCOUNT=%r, USER=%r", settings.SNOWFLAKE_ACCOUNT, settings.SNOWFLAKE_USER)
    return configured


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


def list_all_audits(
    page: int = 1,
    page_size: int = 50,
    strategy_name: str | None = None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
) -> dict:
    """List all audits with pagination and filtering.

    Returns dict with keys: audits (list), total (int), page (int), page_size (int).
    Returns empty list if Snowflake unavailable.
    """
    conn = get_connection()
    if conn is None:
        return {"audits": [], "total": 0, "page": page, "page_size": page_size}

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)

        # Build WHERE clause
        where_clause = ""
        params = []
        if strategy_name:
            where_clause = "WHERE STRATEGY_NAME = %s"
            params.append(strategy_name)

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM AUDIT_RESULTS {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["TOTAL"]

        # Map sort columns
        sort_column_map = {
            "submitted_at": "SUBMITTED_AT",
            "edge_score": "EDGE_SCORE",
            "overfit_probability": "OVERFIT_PROBABILITY",
        }
        db_sort_column = sort_column_map.get(sort_by, "SUBMITTED_AT")
        order = "ASC" if sort_order == "asc" else "DESC"

        # Calculate offset
        offset = (page - 1) * page_size

        # Fetch paginated results
        query = f"""
            SELECT
                AUDIT_ID,
                STRATEGY_NAME,
                EDGE_SCORE,
                OVERFIT_PROBABILITY,
                OVERFIT_LABEL,
                SUBMITTED_AT
            FROM AUDIT_RESULTS
            {where_clause}
            ORDER BY {db_sort_column} {order}
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, [*params, page_size, offset])
        rows = cursor.fetchall()

        # Transform to AuditSummary format
        audits = [
            {
                "audit_id": row["AUDIT_ID"],
                "strategy_name": row["STRATEGY_NAME"],
                "edge_score": float(row["EDGE_SCORE"]) if row["EDGE_SCORE"] else 0.0,
                "overfit_probability": float(row["OVERFIT_PROBABILITY"]) if row["OVERFIT_PROBABILITY"] else 0.0,
                "overfit_label": row["OVERFIT_LABEL"] or "medium",
                "submitted_at": row["SUBMITTED_AT"].isoformat() if row["SUBMITTED_AT"] else "",
            }
            for row in rows
        ]

        return {
            "audits": audits,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error("Failed to list audits: %s", e)
        return {"audits": [], "total": 0, "page": page, "page_size": page_size}


def get_audit_summary() -> dict | None:
    """Get aggregate KPIs for dashboard.

    Returns None if Snowflake unavailable.
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        import snowflake.connector
        cursor = conn.cursor(snowflake.connector.DictCursor)

        cursor.execute("""
            SELECT
                COUNT(*) as total_audits,
                COUNT(DISTINCT STRATEGY_NAME) as unique_strategies,
                AVG(EDGE_SCORE) as average_edge_score,
                AVG(OVERFIT_PROBABILITY) as average_overfit_probability,
                SUM(CASE WHEN OVERFIT_LABEL = 'high' THEN 1 ELSE 0 END) as high_risk_count,
                SUM(CASE WHEN OVERFIT_LABEL = 'medium' THEN 1 ELSE 0 END) as medium_risk_count,
                SUM(CASE WHEN OVERFIT_LABEL = 'low' THEN 1 ELSE 0 END) as low_risk_count,
                MAX(SUBMITTED_AT) as recent_audit_date
            FROM AUDIT_RESULTS
        """)

        result = cursor.fetchone()

        return {
            "total_audits": result["TOTAL_AUDITS"] or 0,
            "unique_strategies": result["UNIQUE_STRATEGIES"] or 0,
            "average_edge_score": float(result["AVERAGE_EDGE_SCORE"]) if result["AVERAGE_EDGE_SCORE"] else 0.0,
            "average_overfit_probability": float(result["AVERAGE_OVERFIT_PROBABILITY"]) if result["AVERAGE_OVERFIT_PROBABILITY"] else 0.0,
            "high_risk_count": result["HIGH_RISK_COUNT"] or 0,
            "medium_risk_count": result["MEDIUM_RISK_COUNT"] or 0,
            "low_risk_count": result["LOW_RISK_COUNT"] or 0,
            "recent_audit_date": result["RECENT_AUDIT_DATE"].isoformat() if result["RECENT_AUDIT_DATE"] else None,
        }
    except Exception as e:
        logger.error("Failed to get audit summary: %s", e)
        return None
