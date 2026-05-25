import datetime
import enum

from sqlalchemy import (
    CheckConstraint,
    Double,
    Enum,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, Relationship, SQLModel


class MeterCommunicationProtocol(str, enum.Enum):
    LORA = 'lora'
    WMBUS = 'wmBus'


class Complex(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('c_id', name='complex_pkey'),
    )

    c_id: int = Field(primary_key=True)
    due_date: str = Field(max_length=50)
    name: str | None = Field(default=None, max_length=200)
    weather_station: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, sa_type=Double(53))
    longitude: float | None = Field(default=None, sa_type=Double(53))

    connection: list['Connection'] = Relationship(back_populates='complex_')


class EnergyMeasurement(SQLModel, table=True):
    __tablename__ = 'energy_measurements'
    __table_args__ = (
        PrimaryKeyConstraint('energy_measurement_id', name='energy_measurements_pkey'),
        Index('idx_em_serial_time', 'serial_number', 'value_time'),
        Index('idx_em_time', 'value_time'),
        Index('idx_em_type_time', 'measurement_type', 'value_time'),
    )

    energy_measurement_id: int = Field(primary_key=True)
    serial_number: str | None = Field(default=None, max_length=12)
    gateway: str | None = Field(default=None, max_length=25)
    measurement_type: str | None = Field(default=None, max_length=32)
    unit: str | None = Field(default=None, max_length=12)
    value: float | None = Field(default=None, sa_type=Double(53))
    value_time: datetime.datetime | None = None
    complex_id: int | None = None
    connection_id: int | None = None


class Meter(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('m_id', name='meter_pkey'),
        UniqueConstraint('serial_number', name='meter_serial_number_key'),
    )

    m_id: int = Field(primary_key=True)
    serial_number: str = Field(max_length=50)
    communication_protocol: MeterCommunicationProtocol = Field(
        sa_type=Enum(
            MeterCommunicationProtocol,
            values_callable=lambda cls: [m.value for m in cls],
            name='meter_communication_protocol',
        )
    )
    offset: float = Field(sa_type=Double(53), sa_column_kwargs={"server_default": text('0')})
    scale: float = Field(sa_type=Double(53), sa_column_kwargs={"server_default": text('1')})
    due_date_month: int | None = Field(default=None, sa_type=SmallInteger)

    meter_installation: list['MeterInstallation'] = Relationship(back_populates='meter_')


class Connection(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['complex'], ['complex.c_id'], ondelete='RESTRICT', name='connection_complex_fkey'),
        PrimaryKeyConstraint('c_id', name='connection_pkey'),
    )

    c_id: int = Field(primary_key=True)
    complex: int
    street: str = Field(max_length=200)
    house_number: int
    house_number_addition: str = Field(
        max_length=20,
        sa_column_kwargs={"server_default": text("''::character varying")},
    )
    zip_code: str = Field(max_length=20)
    town: str = Field(max_length=100)
    country: str = Field(
        max_length=100,
        sa_column_kwargs={"server_default": text("'NL'::character varying")},
    )
    connection_type: str | None = Field(default=None, max_length=50)
    location_info: str | None = Field(default=None, max_length=500)

    complex_: 'Complex' = Relationship(back_populates='connection')
    room: list['Room'] = Relationship(back_populates='connection_')


class Room(SQLModel, table=True):
    __table_args__ = (
        ForeignKeyConstraint(['connection'], ['connection.c_id'], ondelete='RESTRICT', name='room_connection_fkey'),
        PrimaryKeyConstraint('r_id', name='room_pkey'),
    )

    r_id: int = Field(primary_key=True)
    connection: int
    name: str = Field(max_length=100)
    number_of_room: int

    connection_: 'Connection' = Relationship(back_populates='room')
    installation_location: list['InstallationLocation'] = Relationship(back_populates='room_')


class InstallationLocation(SQLModel, table=True):
    __tablename__ = 'installation_location'
    __table_args__ = (
        ForeignKeyConstraint(['room'], ['room.r_id'], ondelete='RESTRICT', name='installation_location_room_fkey'),
        PrimaryKeyConstraint('il_id', name='installation_location_pkey'),
    )

    il_id: int = Field(primary_key=True)
    room: int
    number_within_room: int = Field(sa_column_kwargs={"server_default": text('1')})
    goal: str = Field(max_length=100)
    amount_on_location: int = Field(sa_column_kwargs={"server_default": text('1')})
    correction: float = Field(sa_type=Double(53), sa_column_kwargs={"server_default": text('1')})
    reduction: int = Field(sa_column_kwargs={"server_default": text('0')})
    reference_usage: float | None = Field(default=None, sa_type=Double(53))
    description: str | None = Field(default=None, max_length=500)

    room_: 'Room' = Relationship(back_populates='installation_location')
    meter_installation: list['MeterInstallation'] = Relationship(back_populates='installation_location_')


class MeterInstallation(SQLModel, table=True):
    __tablename__ = 'meter_installation'
    __table_args__ = (
        CheckConstraint('removal_time IS NULL OR removal_time > placement_time', name='chk_removal_after_placement'),
        ForeignKeyConstraint(['installation_location'], ['installation_location.il_id'], ondelete='RESTRICT', name='meter_installation_installation_location_fkey'),
        ForeignKeyConstraint(['meter'], ['meter.m_id'], ondelete='RESTRICT', name='meter_installation_meter_fkey'),
        PrimaryKeyConstraint('mi_id', name='meter_installation_pkey'),
        Index('idx_meter_installation_active', 'installation_location', 'removal_time', postgresql_where='(removal_time IS NULL)'),
        Index('idx_meter_installation_meter', 'meter'),
    )

    mi_id: int = Field(primary_key=True)
    meter: int
    installation_location: int
    placement_time: datetime.datetime
    removal_time: datetime.datetime | None = None

    installation_location_: 'InstallationLocation' = Relationship(back_populates='meter_installation')
    meter_: 'Meter' = Relationship(back_populates='meter_installation')
