import datetime

from sqlalchemy import (
    CheckConstraint,
    Enum,
    Index,
    UniqueConstraint,
)
from sqlmodel import Field, Relationship, SQLModel

from meterapi.enums import MeterCommunicationProtocol


class Complex(SQLModel, table=True):
    c_id: int = Field(primary_key=True)
    due_date: str = Field(max_length=50)
    name: str | None = Field(None, max_length=200)
    weather_station: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None

    connection: list["Connection"] = Relationship(back_populates="complex")
    energy_measurement: list["EnergyMeasurement"] = Relationship(back_populates="complex")


class EnergyMeasurement(SQLModel, table=True):
    __tablename__ = "energy_measurements"
    __table_args__ = (
        Index("idx_em_serial_time", "serial_number", "value_time"),
        Index("idx_em_time", "value_time"),
        Index("idx_em_type_time", "measurement_type", "value_time"),
    )

    energy_measurement_id: int = Field(primary_key=True)
    serial_number: str | None = Field(
        None,
        max_length=50,
        foreign_key="meter.serial_number",
        ondelete="RESTRICT",
    )
    gateway: str | None = Field(None, max_length=25)
    measurement_type: str | None = Field(None, max_length=32)
    unit: str | None = Field(None, max_length=12)
    value: float | None = None
    value_time: datetime.datetime | None = None
    complex_id: int | None = Field(None, foreign_key="complex.c_id", ondelete="RESTRICT")
    connection_id: int | None = Field(None, foreign_key="connection.c_id", ondelete="RESTRICT")

    meter: "Meter" = Relationship(back_populates="energy_measurement")
    complex: "Complex" = Relationship(back_populates="energy_measurement")
    connection: "Connection" = Relationship(back_populates="energy_measurement")


class Meter(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("serial_number"),)

    m_id: int = Field(primary_key=True)
    serial_number: str = Field(max_length=50)
    communication_protocol: MeterCommunicationProtocol = Field(
        sa_type=Enum(
            MeterCommunicationProtocol,
            values_callable=lambda cls: [m.value for m in cls],
            name="meter_communication_protocol",
        )
    )
    offset: float = 0
    scale: float = 1
    due_date_month: int | None = None

    meter_installation: list["MeterInstallation"] = Relationship(back_populates="meter")
    energy_measurement: list["EnergyMeasurement"] = Relationship(back_populates="meter")


class Connection(SQLModel, table=True):
    c_id: int = Field(primary_key=True)
    complex_id: int = Field(
        foreign_key="complex.c_id",
        ondelete="RESTRICT",
        sa_column_kwargs={"name": "complex"},
    )
    street: str = Field(max_length=200)
    house_number: int
    house_number_addition: str = Field("", max_length=20)
    zip_code: str = Field(max_length=20)
    town: str = Field(max_length=100)
    country: str = Field("NL", max_length=100)
    connection_type: str | None = Field(None, max_length=50)
    location_info: str | None = Field(None, max_length=500)

    complex: "Complex" = Relationship(back_populates="connection")
    room: list["Room"] = Relationship(back_populates="connection")
    energy_measurement: list["EnergyMeasurement"] = Relationship(back_populates="connection")


class Room(SQLModel, table=True):
    r_id: int = Field(primary_key=True)
    connection_id: int = Field(
        foreign_key="connection.c_id",
        ondelete="RESTRICT",
        sa_column_kwargs={"name": "connection"},
    )
    name: str = Field(max_length=100)
    number_of_room: int

    connection: "Connection" = Relationship(back_populates="room")
    installation_location: list["InstallationLocation"] = Relationship(back_populates="room")


class InstallationLocation(SQLModel, table=True):
    __tablename__ = "installation_location"

    il_id: int = Field(primary_key=True)
    room_id: int = Field(
        foreign_key="room.r_id",
        ondelete="RESTRICT",
        sa_column_kwargs={"name": "room"},
    )
    number_within_room: int = 1
    goal: str = Field(max_length=100)
    amount_on_location: int = 1
    correction: float = 1
    reduction: int = 0
    reference_usage: float | None = None
    description: str | None = Field(None, max_length=500)

    room: "Room" = Relationship(back_populates="installation_location")
    meter_installation: list["MeterInstallation"] = Relationship(back_populates="installation_location")


class MeterInstallation(SQLModel, table=True):
    __tablename__ = "meter_installation"
    __table_args__ = (
        CheckConstraint(
            "removal_time IS NULL OR removal_time > placement_time",
            name="chk_removal_after_placement",
        ),
        Index(
            "idx_meter_installation_active",
            "installation_location",
            "removal_time",
            postgresql_where="(removal_time IS NULL)",
        ),
        Index("idx_meter_installation_meter", "meter"),
    )

    mi_id: int = Field(primary_key=True)
    meter_id: int = Field(
        foreign_key="meter.m_id",
        ondelete="RESTRICT",
        sa_column_kwargs={"name": "meter"},
    )
    installation_location_id: int = Field(
        foreign_key="installation_location.il_id",
        ondelete="RESTRICT",
        sa_column_kwargs={"name": "installation_location"},
    )
    placement_time: datetime.datetime
    removal_time: datetime.datetime | None = None

    installation_location: "InstallationLocation" = Relationship(back_populates="meter_installation")
    meter: "Meter" = Relationship(back_populates="meter_installation")
