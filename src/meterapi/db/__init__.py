from sqlalchemy import Engine

from meterapi.config import Settings
from meterapi.db.repository import Repository
from meterapi.db.session import (
    ConfigurationError,
    MeterApiError,
    _resolve_credentials,
    create_engine_from_settings,
    get_session,
)

__all__ = [
    "ConfigurationError",
    "MeterApiError",
    "Repository",
    "_resolve_credentials",
    "create_engine_from_settings",
    "get_engine_for_cli",
    "get_session",
]


def get_engine_for_cli() -> Engine:
    """Build an engine from ambient Settings — for CLI / scripts that can't depend on a FastAPI Request."""
    return create_engine_from_settings(Settings())
