from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from meterapi.app.main import app
from meterapi.db import get_session


@pytest.fixture
def db_down_client(engine: Engine) -> Iterator[TestClient]:
    def _raise() -> Iterator[None]:
        raise OperationalError("SELECT 1", None, Exception("db down"))
        yield  # pragma: no cover

    app.state.engine = engine
    app.dependency_overrides[get_session] = _raise
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_operational_error_maps_to_503(db_down_client: TestClient) -> None:
    r = db_down_client.get("/v1/complexes")
    assert r.status_code == 503
    body = r.json()
    assert body == {"detail": "db_unreachable"}
    # No internal/driver detail leaked.
    assert "db down" not in r.text
