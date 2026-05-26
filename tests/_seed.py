"""Shared seed helpers for repository tests."""
import datetime as dt

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


def seed_minimal(session: Session) -> None:
    """One complex → one connection → one room → one meter (active install) → one measurement."""
    session.add(Complex(c_id=1, due_date="2026-01-01", name="Alpha"))
    session.add(
        Connection(c_id=10, complex_id=1, street="X", house_number=1, zip_code="1", town="T")
    )
    session.add(Room(r_id=100, connection_id=10, name="kitchen", number_of_room=1))
    session.add(InstallationLocation(il_id=1000, room_id=100, goal="WKV"))
    session.add(
        Meter(m_id=5, serial_number="SN-A", communication_protocol=MeterCommunicationProtocol.LORA)
    )
    session.add(
        MeterInstallation(
            mi_id=50000,
            meter_id=5,
            installation_location_id=1000,
            placement_time=dt.datetime(2026, 1, 1),
        )
    )
    session.add(
        EnergyMeasurement(
            energy_measurement_id=1,
            serial_number="SN-A",
            measurement_type="energy",
            unit="kWh",
            value=12.5,
            value_time=dt.datetime(2026, 5, 25),
        )
    )
    session.commit()


def is_postgres(session: Session) -> bool:
    return session.bind.dialect.name == "postgresql"
