import datetime as dt

from fastapi.testclient import TestClient
from sqlmodel import Session

from meterapi.models import (
    Complex,
    Meter,
    MeterCommunicationProtocol,
    MeterInstallation,
)
from tests._seed import seed_minimal


# ---------- /health ----------

def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------- /v1/complexes ----------

def test_list_complexes_empty(client: TestClient) -> None:
    r = client.get("/v1/complexes")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body == {"items": [], "total": 0, "limit": 100, "offset": 0}


def test_list_complexes_paginated(client: TestClient, session: Session) -> None:
    for i in (1, 2, 3):
        session.add(Complex(c_id=i, due_date="2026-01-01", name=f"C{i}"))
    session.commit()
    r = client.get("/v1/complexes", params={"limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert [c["id"] for c in body["items"]] == [1, 2]
    assert body["total"] == 3
    assert body["limit"] == 2 and body["offset"] == 0


def test_list_complexes_limit_too_large(client: TestClient) -> None:
    assert client.get("/v1/complexes", params={"limit": 1000}).status_code == 422


def test_complex_connections_404(client: TestClient) -> None:
    r = client.get("/v1/complexes/999/connections")
    assert r.status_code == 404
    assert r.json() == {"detail": "complex 999 not found"}


def test_complex_connections_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/v1/complexes/1/connections")
    assert r.status_code == 200
    body = r.json()
    assert [c["id"] for c in body["items"]] == [10]
    assert body["items"][0]["complexId"] == 1
    assert body["total"] == 1


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
    r = client.get("/v1/complexes/1/meters")
    assert r.status_code == 200
    body = r.json()
    assert {m["id"] for m in body["items"]} == {5}
    assert body["total"] == 1


# ---------- /v1/connections/{connection_id}/rooms ----------

def test_connection_rooms_404(client: TestClient) -> None:
    r = client.get("/v1/connections/999/rooms")
    assert r.status_code == 404


def test_connection_rooms_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/v1/connections/10/rooms")
    assert r.status_code == 200
    body = r.json()
    assert [room["id"] for room in body["items"]] == [100]
    assert body["items"][0]["connectionId"] == 10


# ---------- /v1/meters ----------

def test_meter_detail_404(client: TestClient) -> None:
    r = client.get("/v1/meters/unknown")
    assert r.status_code == 404


def test_meter_detail_happy(client: TestClient, session: Session) -> None:
    seed_minimal(session)
    r = client.get("/v1/meters/SN-A")
    assert r.status_code == 200
    body = r.json()
    assert body["serialNumber"] == "SN-A"
    assert body["installationGoal"] == "WKV"
    assert body["roomLabel"] == "kitchen_1"
    assert body["lastReading"]["value"] == 12.5
    assert body["lastReading"]["measurementType"] == "energy"


def test_meters_stale_default_24h(client: TestClient, session: Session) -> None:
    # No readings → meter is stale
    session.add(Meter(
        m_id=5, serial_number="SN-NONE",
        communication_protocol=MeterCommunicationProtocol.LORA,
    ))
    session.commit()
    r = client.get("/v1/meters/stale")
    assert r.status_code == 200
    body = r.json()
    assert [m["serialNumber"] for m in body["items"]] == ["SN-NONE"]
    assert body["total"] == 1


def test_meters_stale_zero_hours_rejected(client: TestClient) -> None:
    assert client.get("/v1/meters/stale", params={"hours": 0}).status_code == 422


def test_meters_stale_hours_over_cap_rejected(client: TestClient) -> None:
    assert client.get("/v1/meters/stale", params={"hours": 9000}).status_code == 422


# ---------- /v1/measurements ----------

def test_measurements_list_default_window(
    client: TestClient, session: Session,
) -> None:
    seed_minimal(session)
    r = client.get("/v1/measurements", params={
        "serial_number": "SN-A",
        "from": "2026-05-01T00:00:00",
        "to": "2026-06-01T00:00:00",
    })
    assert r.status_code == 200
    body = r.json()
    assert [m["energyMeasurementId"] for m in body["items"]] == [1]
    assert body["total"] == 1


def test_measurements_unknown_meter_404(client: TestClient) -> None:
    r = client.get("/v1/measurements", params={
        "serial_number": "nope",
        "from": "2026-05-01T00:00:00",
        "to": "2026-06-01T00:00:00",
    })
    assert r.status_code == 404


def test_measurements_from_after_to_400(client: TestClient) -> None:
    r = client.get("/v1/measurements", params={
        "serial_number": "x",
        "from": "2026-06-01T00:00:00",
        "to": "2026-05-01T00:00:00",
    })
    assert r.status_code == 400


def test_measurements_aggregate_missing_grain_422(client: TestClient) -> None:
    r = client.get("/v1/measurements/aggregate", params={"serial_number": "x"})
    assert r.status_code == 422


def test_measurements_aggregate_invalid_grain_422(client: TestClient) -> None:
    r = client.get(
        "/v1/measurements/aggregate", params={"serial_number": "x", "grain": "year"}
    )
    assert r.status_code == 422


# ---------- OpenAPI surface ----------

def test_openapi_lists_endpoints(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    paths = spec["paths"].keys()
    assert "/health" in paths
    assert "/ready" in paths
    assert "/v1/complexes" in paths
    assert "/v1/complexes/{complex_id}/connections" in paths
    assert "/v1/complexes/{complex_id}/meters" in paths
    assert "/v1/connections/{connection_id}/rooms" in paths
    assert "/v1/meters/{serial_number}" in paths
    assert "/v1/meters/stale" in paths
    assert "/v1/measurements" in paths
    assert "/v1/measurements/aggregate" in paths
