from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlmodel import select

from meterapi.db.mixins.base import _RepoBase
from meterapi.models import (
    Connection,
    EnergyMeasurement,
    InstallationLocation,
    Meter,
    MeterInstallation,
    Room,
)


@dataclass(frozen=True, slots=True)
class MeterDetail:
    meter: Meter
    last_reading: EnergyMeasurement | None
    installation_location: str | None
    room_label: str | None


@dataclass(frozen=True, slots=True)
class StaleMeterRow:
    m_id: int
    serial_number: str
    last_value_time: datetime | None


class MeterMixin(_RepoBase):
    def list_meters_for_complex(
        self, c_id: int, *, limit: int, offset: int,
    ) -> list[Meter]:
        active_meter_ids = (
            select(MeterInstallation.meter_id)
            .where(MeterInstallation.removal_time.is_(None))
            .join(InstallationLocation, InstallationLocation.il_id == MeterInstallation.installation_location_id)
            .join(Room, Room.r_id == InstallationLocation.room_id)
            .join(Connection, Connection.c_id == Room.connection_id)
            .where(Connection.complex_id == c_id)
        )
        stmt = (
            select(Meter)
            .where(Meter.m_id.in_(active_meter_ids))
            .order_by(Meter.m_id)
            .limit(limit).offset(offset)
        )
        return list(self.session.exec(stmt).all())

    def get_meter_by_serial(self, serial: str) -> MeterDetail | None:
        meter = self.session.exec(
            select(Meter).where(Meter.serial_number == serial)
        ).first()
        if meter is None:
            return None

        last = self.session.exec(
            select(EnergyMeasurement)
            .where(EnergyMeasurement.serial_number == serial)
            .order_by(EnergyMeasurement.value_time.desc())
            .limit(1)
        ).first()

        ctx = self.session.exec(
            select(InstallationLocation.goal, Room.name, Room.number_of_room)
            .join(MeterInstallation, MeterInstallation.installation_location_id == InstallationLocation.il_id)
            .where(MeterInstallation.meter_id == meter.m_id)
            .where(MeterInstallation.removal_time.is_(None))
            .join(Room, Room.r_id == InstallationLocation.room_id)
            .limit(1)
        ).first()
        if ctx is not None:
            goal, room_name, room_number = ctx
            room_label = f"{room_name}_{room_number}"
        else:
            goal = None
            room_label = None
        return MeterDetail(
            meter=meter,
            last_reading=last,
            installation_location=goal,
            room_label=room_label,
        )

    def list_stale_meters(
        self, *, hours: int, limit: int, offset: int,
        now: datetime | None = None,
    ) -> list[StaleMeterRow]:
        cutoff = (now or datetime.now(UTC)) - timedelta(hours=hours)
        last_value = func.max(EnergyMeasurement.value_time).label("last_value_time")
        stmt = (
            select(Meter.m_id, Meter.serial_number, last_value)
            .join(
                EnergyMeasurement,
                EnergyMeasurement.serial_number == Meter.serial_number,
                isouter=True,
            )
            .group_by(Meter.m_id, Meter.serial_number)
            .having((func.max(EnergyMeasurement.value_time).is_(None))
                    | (func.max(EnergyMeasurement.value_time) < cutoff))
            .order_by(last_value.is_(None).desc(), last_value, Meter.m_id)
            .limit(limit).offset(offset)
        )
        rows = self.session.exec(stmt).all()
        return [
            StaleMeterRow(m_id=r[0], serial_number=r[1], last_value_time=r[2])
            for r in rows
        ]
