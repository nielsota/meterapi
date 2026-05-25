from sqlmodel import Session, select

from meterapi.models import (
    EnergyMeasurement,
    InstallationLocation,
    Meter,
    MeterInstallation,
    MeterLastValue,
    Room,
)


class MeterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_last_meter_values(
        self, connection_id: int, meter_type: str
    ) -> list[MeterLastValue]:
        stmt = (
            select(
                InstallationLocation.goal.label("type"),
                Meter.serial_number.label("serial"),
                Room.name.label("room_name"),
                Room.number_of_room.label("room_number"),
                EnergyMeasurement.value.label("value"),
                EnergyMeasurement.unit.label("unit"),
            )
            .join(Meter, Meter.serial_number == EnergyMeasurement.serial_number)
            .join(MeterInstallation, MeterInstallation.meter_id == Meter.m_id)
            .join(InstallationLocation, MeterInstallation.installation_location_id == InstallationLocation.il_id)
            .join(Room, InstallationLocation.room_id == Room.r_id)
            .where(Room.connection_id == connection_id)
            .where(InstallationLocation.goal == meter_type)
            .distinct(Meter.m_id)
            .order_by(Meter.m_id, EnergyMeasurement.value_time.desc())
        )
        rows = self.session.exec(stmt).all()
        return [
            MeterLastValue(
                type=row.type,
                serial=row.serial,
                room=f"{row.room_name}_{row.room_number}",
                value=row.value,
                unit=row.unit,
            )
            for row in rows
        ]
