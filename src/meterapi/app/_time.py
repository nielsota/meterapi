"""Datetime helpers for the API boundary."""
from datetime import UTC, datetime


def to_utc(value: datetime) -> datetime:
    """Coerce a datetime to UTC.

    Naive datetimes are assumed to already be UTC; aware datetimes are converted.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
