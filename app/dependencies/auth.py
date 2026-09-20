"""
Legacy Auth Dependencies Module

Re-exports `get_current_user` from `app.core.dependencies` for backward compatibility.
"""

from app.core.dependencies import get_current_user, security_scheme

__all__ = ["get_current_user", "security_scheme"]
