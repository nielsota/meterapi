from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from meterapi.enums import MeterCommunicationProtocol

__all__ = [
    "ComplexResponse",
    "ConnectionResponse",
    "ErrorResponse",
    "Grain",
    "LastReading",
    "MeasurementAggregateResponse",
    "MeasurementResponse",
    "MeterDetailResponse",
    "MeterResponse",
    "RoomResponse",
    "StaleMeterResponse",
]


# ---------- Shared ----------

Grain = Literal["day", "month"]


class ErrorResponse(BaseModel):
    detail: str


# ---------- Complexes ----------

class ComplexResponse(BaseModel):
    model_config = {"from_attributes": True}

    c_id: int
    name: str | None = None
    due_date: str
    weather_station: str | None = None
    latitude: float | None = None
    longitude: float | None = None


# ---------- Connections ----------

class ConnectionResponse(BaseModel):
    model_config = {"from_attributes": True}

    c_id: int
    complex_id: int
    street: str
    house_number: int
    house_number_addition: str = ""
    zip_code: str
    town: str
    country: str = "NL"
    connection_type: str | None = None
    location_info: str | None = None


# ---------- Rooms ----------

class RoomResponse(BaseModel):
    model_config = {"from_attributes": True}

    r_id: int
    connection_id: int
    name: str
    number_of_room: int


# ---------- Meters ----------

class MeterResponse(BaseModel):
    model_config = {"from_attributes": True}

    m_id: int
    serial_number: str
    communication_protocol: MeterCommunicationProtocol
    offset: float
    scale: float
    due_date_month: int | None = None


class LastReading(BaseModel):
    value: float | None
    unit: str | None
    value_time: datetime | None
    measurement_type: str | None


class MeterDetailResponse(MeterResponse):
    installation_location: str | None = None
    room: str | None = None
    last_reading: LastReading | None = None


class StaleMeterResponse(BaseModel):
    m_id: int
    serial_number: str
    last_value_time: datetime | None = None


# ---------- Measurements ----------

class MeasurementResponse(BaseModel):
    model_config = {"from_attributes": True}

    energy_measurement_id: int
    serial_number: str | None
    measurement_type: str | None
    unit: str | None
    value: float | None
    value_time: datetime | None


class MeasurementAggregateResponse(BaseModel):
    bucket: datetime
    sum: float
    avg: float
    count: int
