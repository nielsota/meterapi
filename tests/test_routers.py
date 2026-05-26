import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from meterapi.models import (
    Complex,
    Connection,
    EnergyMeasurement,
    InstallationLocation,
    Meter,
    MeterCommunicationProtocol,
    MeterInstallation,
    Room,
)
from tests._seed import seed_minimal


# ---------- /health ----------

def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------- /complexes ----------

def test_list_complexes_empty(client: TestClient) -> None:
    r = client.get("/complexes")
    assert r.status_code == 200
    assert r.json() == []


def test_list_complexes_paginated(client: TestClient, session: Session) -> None:
    for i in (1, 2, 3):
        session.add(Complex(c_id=i, due_date="2026-01-01", name=f"C{i}"))
    session.commit()
    r = client.get("/complexes", params={"limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert [c["c_id"] for c in body] == [1, 2]


def test_list_complexes_limit_too_large(client: TestClient) -> None:
    assert client.get("/complexes", params={"limit": 1000}).status_code == 422


def test_complex_connections_404(client: TestClient) -> None:
    r = client.get("/complexes/999/connections")
    assert r.status_code == 404
    assert r.json() == {"detail": "complex 999 not found"}


def test_complex_connections_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/complexes/1/connections")
    assert r.status_code == 200
    assert [c["c_id"] for c in r.json()] == [10]


def test_complex_meters_excludes_decommissioned(
    client: TestClient, session: Session,
) -> None:
    seed_minimal(session)
    session.add(Meter(
        m_id=6, serial_number="SN-OLD",
        communication_protocol=MeterCommunicationProtocol.WMBUS,
    ))
    session.add(MeterInstallation(
        mi_id=50001, meter_id=6, installation_location_id=1000,
        placement_time=dt.datetime(2025, 1, 1),
        removal_time=dt.datetime(2026, 1, 1),
    ))
    session.commit()
    r = client.get("/complexes/1/meters")
    assert r.status_code == 200
    assert {m["m_id"] for m in r.json()} == {5}


# ---------- /connections/{c_id}/rooms ----------

def test_connection_rooms_404(client: TestClient) -> None:
    r = client.get("/connections/999/rooms")
    assert r.status_code == 404


def test_connection_rooms_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/connections/10/rooms")
    assert r.status_code == 200
    assert [room["r_id"] for room in r.json()] == [100]


# ---------- /meters ----------

def test_meter_detail_404(client: TestClient) -> None:
    r = client.get("/meters/unknown")
    assert r.status_code == 404


def test_meter_detail_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/meters/SN-A")
    assert r.status_code == 200
    body = r.json()
    assert body["serial_number"] == "SN-A"
    assert body["installation_location"] == "WKV"
    assert body["room"] == "kitchen_1"
    assert body["last_reading"]["value"] == 12.5


def test_meters_stale_default_24h(client: TestClient, session: Session) -> None:
    # No readings → meter is stale
    session.add(Meter(
        m_id=5, serial_number="SN-NONE",
        communication_protocol=MeterCommunicationProtocol.LORA,
    ))
    session.commit()
    r = client.get("/meters/stale")
    assert r.status_code == 200
    assert [m["serial_number"] for m in r.json()] == ["SN-NONE"]


def test_meters_stale_zero_hours_rejected(client: TestClient) -> None:
    assert client.get("/meters/stale", params={"hours": 0}).status_code == 422


# ---------- /measurements ----------

def test_measurements_list_default_window(
    client: TestClient, session: Session,
) -> None:
    seed_minimal(session)
    # Default from/to covers last 7 days; seed_minimal value_time is 2026-05-25.
    # Using a date inside the window via 'to' to make this deterministic.
    r = client.get("/measurements", params={
        "serial": "SN-A",
        "from": "2026-05-01T00:00:00",
        "to": "2026-06-01T00:00:00",
    })
    assert r.status_code == 200
    assert [m["energy_measurement_id"] for m in r.json()] == [1]


def test_measurements_from_after_to_400(client: TestClient) -> None:
    r = client.get("/measurements", params={
        "serial": "x",
        "from": "2026-06-01T00:00:00",
        "to": "2026-05-01T00:00:00",
    })
    assert r.status_code == 400


def test_measurements_aggregate_missing_grain_422(client: TestClient) -> None:
    assert client.get("/measurements/aggregate", params={"serial": "x"}).status_code == 422


def test_measurements_aggregate_invalid_grain_422(client: TestClient) -> None:
    r = client.get("/measurements/aggregate", params={"serial": "x", "grain": "year"})
    assert r.status_code == 422


# ---------- Legacy removal ----------

def test_legacy_last_values_gone(client: TestClient) -> None:
    assert client.get("/meters/last-values").status_code == 404


def test_openapi_lists_new_endpoints(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = spec["paths"].keys()
    assert "/health" in paths
    assert "/complexes" in paths
    assert "/complexes/{c_id}/connections" in paths
    assert "/complexes/{c_id}/meters" in paths
    assert "/connections/{c_id}/rooms" in paths
    assert "/meters/{serial}" in paths
    assert "/meters/stale" in paths
    assert "/measurements" in paths
    assert "/measurements/aggregate" in paths
