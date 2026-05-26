import datetime as dt

import pytest
from sqlmodel import Session

from meterapi.db import Repository
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
from tests._seed import is_postgres, seed_minimal


# ---------- Complexes ----------

def test_list_complexes_paginates(session: Session) -> None:
    for i in (1, 2, 3):
        session.add(Complex(c_id=i, due_date="2026-01-01", name=f"C{i}"))
    session.commit()
    repo = Repository(session)
    page1 = repo.list_complexes(limit=2, offset=0)
    page2 = repo.list_complexes(limit=2, offset=2)
    assert [c.c_id for c in page1] == [1, 2]
    assert [c.c_id for c in page2] == [3]


def test_get_complex_returns_none_when_missing(session: Session) -> None:
    assert Repository(session).get_complex(999) is None


def test_get_complex_returns_match(session: Session) -> None:
    seed_minimal(session)
    c = Repository(session).get_complex(1)
    assert c is not None and c.c_id == 1


# ---------- Connections ----------

def test_list_connections_for_complex_filters_and_paginates(session: Session) -> None:
    session.add(Complex(c_id=1, due_date="2026-01-01"))
    session.add(Complex(c_id=2, due_date="2026-01-01"))
    for i in (10, 11):
        session.add(Connection(
            c_id=i, complex_id=1, street="S", house_number=i, zip_code="1", town="T",
        ))
    session.add(Connection(
        c_id=20, complex_id=2, street="S", house_number=1, zip_code="1", town="T",
    ))
    session.commit()
    repo = Repository(session)
    rows = repo.list_connections_for_complex(1, limit=10, offset=0)
    assert {c.c_id for c in rows} == {10, 11}


def test_get_connection_lookup(session: Session) -> None:
    seed_minimal(session)
    assert Repository(session).get_connection(10) is not None
    assert Repository(session).get_connection(999) is None


# ---------- Rooms ----------

def test_list_rooms_for_connection(session: Session) -> None:
    seed_minimal(session)
    session.add(Room(r_id=101, connection_id=10, name="bath", number_of_room=2))
    session.commit()
    rooms = Repository(session).list_rooms_for_connection(10, limit=10, offset=0)
    assert {r.r_id for r in rooms} == {100, 101}


# ---------- Meters ----------

def test_list_meters_for_complex_excludes_decommissioned(session: Session) -> None:
    seed_minimal(session)
    # Add a second meter whose installation has been removed — should not appear.
    session.add(Meter(
        m_id=6, serial_number="SN-OLD",
        communication_protocol=MeterCommunicationProtocol.WMBUS,
    ))
    session.add(MeterInstallation(
        mi_id=50001,
        meter_id=6,
        installation_location_id=1000,
        placement_time=dt.datetime(2025, 1, 1),
        removal_time=dt.datetime(2026, 1, 1),
    ))
    session.commit()
    meters = Repository(session).list_meters_for_complex(1, limit=10, offset=0)
    assert {m.m_id for m in meters} == {5}


def test_get_meter_by_serial_returns_detail(session: Session) -> None:
    seed_minimal(session)
    detail = Repository(session).get_meter_by_serial("SN-A")
    assert detail is not None
    assert detail.meter.m_id == 5
    assert detail.last_reading is not None
    assert detail.last_reading.value == 12.5
    assert detail.installation_location == "WKV"
    assert detail.room_label == "kitchen_1"


def test_get_meter_by_serial_unknown_returns_none(session: Session) -> None:
    assert Repository(session).get_meter_by_serial("nope") is None


def test_get_meter_by_serial_no_readings(session: Session) -> None:
    # Seed without the EnergyMeasurement (custom partial seed).
    session.add(Complex(c_id=1, due_date="2026-01-01"))
    session.add(Connection(
        c_id=10, complex_id=1, street="X", house_number=1, zip_code="1", town="T",
    ))
    session.add(Room(r_id=100, connection_id=10, name="kitchen", number_of_room=1))
    session.add(InstallationLocation(il_id=1000, room_id=100, goal="WKV"))
    session.add(Meter(
        m_id=5, serial_number="SN-A",
        communication_protocol=MeterCommunicationProtocol.LORA,
    ))
    session.add(MeterInstallation(
        mi_id=50000,
        meter_id=5,
        installation_location_id=1000,
        placement_time=dt.datetime(2026, 1, 1),
    ))
    session.commit()
    detail = Repository(session).get_meter_by_serial("SN-A")
    assert detail is not None
    assert detail.last_reading is None
    assert detail.installation_location == "WKV"


def test_list_stale_meters_includes_meter_with_no_readings(session: Session) -> None:
    session.add(Meter(
        m_id=5, serial_number="SN-NONE",
        communication_protocol=MeterCommunicationProtocol.LORA,
    ))
    session.commit()
    rows = Repository(session).list_stale_meters(
        hours=24, limit=10, offset=0, now=dt.datetime(2026, 5, 25, tzinfo=dt.UTC),
    )
    assert len(rows) == 1
    assert rows[0].serial_number == "SN-NONE"
    assert rows[0].last_value_time is None


def test_list_stale_meters_excludes_fresh(session: Session) -> None:
    seed_minimal(session)
    # Add a fresh reading for SN-A so it should NOT be stale.
    session.add(EnergyMeasurement(
        energy_measurement_id=2,
        serial_number="SN-A",
        value=1.0,
        value_time=dt.datetime(2026, 5, 26, 10),
    ))
    session.commit()
    rows = Repository(session).list_stale_meters(
        hours=24, limit=10, offset=0, now=dt.datetime(2026, 5, 26, 11, tzinfo=dt.UTC),
    )
    assert rows == []


# ---------- Measurements ----------

def test_list_measurements_filters_and_orders(session: Session) -> None:
    seed_minimal(session)
    session.add(EnergyMeasurement(
        energy_measurement_id=2,
        serial_number="SN-A",
        measurement_type="energy",
        value=20,
        value_time=dt.datetime(2026, 5, 26),
    ))
    session.commit()
    rows = Repository(session).list_measurements(
        serial="SN-A",
        from_=dt.datetime(2026, 5, 1),
        to=dt.datetime(2026, 6, 1),
        measurement_type=None,
        limit=10, offset=0,
    )
    assert [r.energy_measurement_id for r in rows] == [2, 1]


def test_list_measurements_respects_type_filter(session: Session) -> None:
    seed_minimal(session)
    session.add(EnergyMeasurement(
        energy_measurement_id=2,
        serial_number="SN-A",
        measurement_type="water",
        value=99,
        value_time=dt.datetime(2026, 5, 26),
    ))
    session.commit()
    rows = Repository(session).list_measurements(
        serial="SN-A",
        from_=dt.datetime(2026, 5, 1),
        to=dt.datetime(2026, 6, 1),
        measurement_type="water",
        limit=10, offset=0,
    )
    assert [r.energy_measurement_id for r in rows] == [2]


def test_aggregate_measurements_rejects_bad_grain(session: Session) -> None:
    with pytest.raises(ValueError, match="invalid grain"):
        Repository(session).aggregate_measurements(
            serial="x", grain="year",  # type: ignore[arg-type]
            from_=dt.datetime(2026, 1, 1), to=dt.datetime(2026, 2, 1),
            measurement_type=None,
        )


@pytest.mark.postgres
def test_aggregate_measurements_buckets_by_day(session: Session) -> None:
    if not is_postgres(session):
        pytest.skip("date_trunc requires postgres")
    seed_minimal(session)
    rows = Repository(session).aggregate_measurements(
        serial="SN-A", grain="day",
        from_=dt.datetime(2026, 5, 1), to=dt.datetime(2026, 6, 1),
        measurement_type=None,
    )
    assert len(rows) == 1
    assert rows[0].sum == 12.5
