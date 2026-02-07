"""
Parsers — utility functions for parsing and validating
incoming strategy data.
"""

from datetime import datetime


def parse_date(date_str: str) -> datetime:
    """Parse an ISO-format date string.

    TODO: Add support for additional date formats.
    """
    return datetime.fromisoformat(date_str)


def validate_returns(raw_returns: list[float]) -> list[float]:
    """Sanitise a list of return values.

    TODO: Add outlier detection / clamping.
    """
    return [float(r) for r in raw_returns if r is not None]
