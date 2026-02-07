"""
Backboard Client — pushes audit results and strategy data to
Backboard.io for dashboard visualization and reporting.

Backboard.io serves as the frontend presentation layer.
This client pushes structured data so dashboards can render
Edge Scores, audit reports, comparisons, and leaderboards.
"""

import httpx

from ..core.config import settings
from ..core.logging import logger

_TIMEOUT = 15.0  # seconds


def _is_configured() -> bool:
    """Check if Backboard API key is configured."""
    return bool(settings.BACKBOARD_API_KEY)


def _headers() -> dict:
    """Build auth headers for Backboard API."""
    return {
        "Authorization": f"Bearer {settings.BACKBOARD_API_KEY}",
        "Content-Type": "application/json",
    }


def _base_url() -> str:
    return settings.BACKBOARD_BASE_URL.rstrip("/")


def is_configured() -> bool:
    """Public check for Backboard configuration status."""
    return _is_configured()


def push_audit_result(audit_result: dict) -> bool:
    """Push a completed audit result to Backboard for dashboard rendering.

    Sends the full audit payload including Edge Score breakdown,
    overfit score, regime analysis, Monte Carlo stats, and narrative
    to the Backboard data ingestion endpoint.

    Args:
        audit_result: Full AuditResult dict from the audit pipeline.

    Returns:
        True if push succeeded, False otherwise.
    """
    if not _is_configured():
        logger.debug("Backboard not configured — skipping push")
        return False

    payload = {
        "dataset": "audit_results",
        "records": [
            {
                "audit_id": audit_result.get("audit_id", ""),
                "strategy_name": audit_result.get("strategy_name", ""),
                "edge_score": _extract_edge_score(audit_result),
                "overfit_probability": _extract_nested(
                    audit_result, "overfit_score", "probability"
                ),
                "overfit_label": _extract_nested(
                    audit_result, "overfit_score", "label"
                ),
                "regime_sensitivity": _extract_nested(
                    audit_result, "regime_analysis", "regime_sensitivity"
                ),
                "current_regime": _extract_nested(
                    audit_result, "regime_analysis", "current_regime"
                ),
                "per_regime_sharpe": _extract_nested(
                    audit_result, "regime_analysis", "per_regime_sharpe"
                ),
                "mc_p_value": _extract_nested(
                    audit_result, "monte_carlo", "p_value"
                ),
                "mc_sharpe_percentile": _extract_nested(
                    audit_result, "monte_carlo", "sharpe_percentile"
                ),
                "confidence_interval_95": _extract_nested(
                    audit_result, "monte_carlo", "confidence_interval_95"
                ),
                "narrative": audit_result.get("narrative", ""),
                "recommendations": audit_result.get("recommendations", []),
                "sub_scores": _extract_sub_scores(audit_result),
            }
        ],
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{_base_url()}/data/ingest",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            logger.info(
                "Pushed audit %s to Backboard (status=%d)",
                audit_result.get("audit_id", ""),
                response.status_code,
            )
            return True
    except httpx.HTTPStatusError as e:
        logger.warning(
            "Backboard push failed (HTTP %d): %s",
            e.response.status_code,
            e.response.text[:200],
        )
        return False
    except Exception as e:
        logger.warning("Backboard push failed: %s", e)
        return False


def push_strategy_summary(strategy_summaries: list[dict]) -> bool:
    """Push strategy summary data for the leaderboard/dashboard.

    Args:
        strategy_summaries: List of dicts with strategy_name,
                            edge_score, last_audited, audit_count.

    Returns:
        True if push succeeded, False otherwise.
    """
    if not _is_configured():
        return False

    payload = {
        "dataset": "strategy_summaries",
        "records": strategy_summaries,
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{_base_url()}/data/ingest",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            logger.info("Pushed %d strategy summaries to Backboard", len(strategy_summaries))
            return True
    except Exception as e:
        logger.warning("Backboard strategy summary push failed: %s", e)
        return False


def push_leaderboard(leaderboard: list[dict]) -> bool:
    """Push leaderboard data to Backboard for the ranking dashboard.

    Args:
        leaderboard: List of dicts with strategy_name, edge_score, etc.

    Returns:
        True if push succeeded, False otherwise.
    """
    if not _is_configured():
        return False

    payload = {
        "dataset": "leaderboard",
        "records": leaderboard,
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{_base_url()}/data/ingest",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            logger.info("Pushed leaderboard (%d entries) to Backboard", len(leaderboard))
            return True
    except Exception as e:
        logger.warning("Backboard leaderboard push failed: %s", e)
        return False


def push_market_data_summary(tickers: list[str], date_range: dict) -> bool:
    """Push market data availability summary to Backboard.

    Args:
        tickers: List of available ticker symbols.
        date_range: Dict with min_date and max_date.

    Returns:
        True if push succeeded, False otherwise.
    """
    if not _is_configured():
        return False

    payload = {
        "dataset": "market_data_summary",
        "records": [
            {
                "available_tickers": tickers,
                "date_range_start": date_range.get("min_date", ""),
                "date_range_end": date_range.get("max_date", ""),
                "ticker_count": len(tickers),
            }
        ],
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.post(
                f"{_base_url()}/data/ingest",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.warning("Backboard market data summary push failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_edge_score(audit_result: dict) -> float:
    """Extract the composite edge score from nested result."""
    edge = audit_result.get("edge_score")
    if isinstance(edge, dict):
        return edge.get("edge_score", 0.0)
    return 0.0


def _extract_nested(d: dict, key1: str, key2: str, default=None):
    """Safely extract a nested value."""
    inner = d.get(key1)
    if isinstance(inner, dict):
        return inner.get(key2, default)
    return default


def _extract_sub_scores(audit_result: dict) -> dict:
    """Extract all sub-scores for dashboard visualization."""
    edge = audit_result.get("edge_score")
    if not isinstance(edge, dict):
        return {}
    return {
        "overfit": edge.get("overfit_sub_score", 0),
        "regime": edge.get("regime_sub_score", 0),
        "stat_sig": edge.get("stat_sig_sub_score", 0),
        "data_leakage": edge.get("data_leakage_sub_score", 0),
        "explainability": edge.get("explainability_sub_score", 0),
    }
