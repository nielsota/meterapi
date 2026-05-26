from unittest.mock import MagicMock

from meterapi.db import Repository


def test_repository_holds_session() -> None:
    s = MagicMock()
    assert Repository(s).session is s
