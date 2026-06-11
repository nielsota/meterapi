from datetime import UTC, datetime, timedelta, timezone

from meterapi.app._time import to_utc


def test_to_utc_assumes_naive_is_utc() -> None:
    naive = datetime(2026, 5, 25, 12, 0, 0)
    result = to_utc(naive)
    assert result.tzinfo == UTC
    assert result == datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)


def test_to_utc_converts_aware() -> None:
    plus_two = timezone(timedelta(hours=2))
    aware = datetime(2026, 5, 25, 12, 0, 0, tzinfo=plus_two)
    result = to_utc(aware)
    assert result.tzinfo == UTC
    assert result == datetime(2026, 5, 25, 10, 0, 0, tzinfo=UTC)
