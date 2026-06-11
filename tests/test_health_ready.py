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


def test_health_ok_without_db(db_down_client: TestClient) -> None:
    # Liveness must not depend on the database.
    r = db_down_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_ok_with_db(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready"}


def test_ready_503_when_db_unreachable(db_down_client: TestClient) -> None:
    r = db_down_client.get("/ready")
    assert r.status_code == 503
    assert r.json() == {"detail": "db_unreachable"}
