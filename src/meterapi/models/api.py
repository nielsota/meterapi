import datetime
from typing import Generic, Literal, TypeVar

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from meterapi.enums import MeterCommunicationProtocol

__all__ = [
    "ApiModel",
    "ComplexResponse",
    "ConnectionResponse",
    "ErrorResponse",
    "Grain",
    "LastReading",
    "MeasurementAggregateResponse",
    "MeasurementResponse",
    "MeterDetailResponse",
    "MeterResponse",
    "Page",
    "RoomResponse",
    "StaleMeterResponse",
    "ValidationErrorResponse",
]


# ---------- Base ----------

class ApiModel(BaseModel):
    """Base for all API schemas.

    Validation reads by field name (snake_case) so `model_validate(orm_obj)` keeps
    working against ORM attributes; serialization emits camelCase for the SPA.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        populate_by_name=True,
        from_attributes=True,
    )


# ---------- Shared ----------

Grain = Literal["day", "month"]


class ErrorResponse(ApiModel):
    detail: str


class ValidationErrorResponse(ApiModel):
    """Mirrors FastAPI's native 422 body shape for OpenAPI documentation."""

    detail: list[dict]


T = TypeVar("T")


class Page(ApiModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ---------- Complexes ----------

class ComplexResponse(ApiModel):
    id: int = Field(validation_alias="c_id")
    name: str | None = None
    due_date: datetime.date
    weather_station: str | None = None
    latitude: float | None = None
    longitude: float | None = None


# ---------- Connections ----------

class ConnectionResponse(ApiModel):
    id: int = Field(validation_alias="c_id")
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

class RoomResponse(ApiModel):
    id: int = Field(validation_alias="r_id")
    connection_id: int
    name: str
    number_of_room: int


# ---------- Meters ----------

class MeterResponse(ApiModel):
    id: int = Field(validation_alias="m_id")
    serial_number: str
    communication_protocol: MeterCommunicationProtocol
    calibration_offset: float = Field(validation_alias="offset")
    scale: float
    due_date_month: int | None = None


class LastReading(ApiModel):
    value: float | None
    unit: str | None
    value_time: datetime.datetime | None
    measurement_type: str | None


class MeterDetailResponse(MeterResponse):
    installation_goal: str | None = None
    room_label: str | None = None
    last_reading: LastReading | None = None


class StaleMeterResponse(ApiModel):
    id: int = Field(validation_alias="m_id")
    serial_number: str
    last_value_time: datetime.datetime | None = None


# ---------- Measurements ----------

class MeasurementResponse(ApiModel):
    energy_measurement_id: int
    serial_number: str | None
    measurement_type: str | None
    unit: str | None
    value: float | None
    value_time: datetime.datetime | None


class MeasurementAggregateResponse(ApiModel):
    bucket: datetime.datetime
    sum: float
    avg: float
    count: int
