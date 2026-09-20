"""
DateTime Utilities Module

Provides helper functions for generating standard timezone-aware UTC timestamps.
"""

from datetime import datetime, timezone


def get_utc_now() -> datetime:
    """
    Returns current timezone-aware UTC datetime.

    Returns:
        datetime object configured with UTC timezone.
    """
    return datetime.now(timezone.utc)
