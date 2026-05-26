import datetime as dt

import pytest
from pydantic import ValidationError

from meterapi.models import (
    Complex,
    Connection,
    Meter,
    MeterCommunicationProtocol,
    Room,
)
from meterapi.models.api import (
    ComplexResponse,
    ConnectionResponse,
    LastReading,
    MeasurementAggregateResponse,
    MeterDetailResponse,
    MeterResponse,
    RoomResponse,
    StaleMeterResponse,
)


def test_complex_response_from_orm() -> None:
    c = Complex(c_id=1, due_date="2026-01-01", name="A")
    assert ComplexResponse.model_validate(c).c_id == 1


def test_connection_response_from_orm() -> None:
    c = Connection(c_id=10, complex_id=1, street="X", house_number=2, zip_code="1", town="T")
    assert ConnectionResponse.model_validate(c).house_number == 2


def test_room_response_from_orm() -> None:
    r = Room(r_id=1, connection_id=10, name="k", number_of_room=1)
    assert RoomResponse.model_validate(r).name == "k"


def test_meter_response_from_orm() -> None:
    m = Meter(m_id=5, serial_number="SN", communication_protocol=MeterCommunicationProtocol.LORA)
    assert MeterResponse.model_validate(m).serial_number == "SN"


def test_meter_detail_extends_meter() -> None:
    m = Meter(m_id=5, serial_number="SN", communication_protocol=MeterCommunicationProtocol.LORA)
    d = MeterDetailResponse.model_validate(
        {**MeterResponse.model_validate(m).model_dump(),
         "installation_location": "WKV", "room": "kitchen_1",
         "last_reading": LastReading(value=1.0, unit="kWh", value_time=dt.datetime(2026, 1, 1), measurement_type="energy")}
    )
    assert d.installation_location == "WKV"
    assert d.last_reading is not None and d.last_reading.value == 1.0


def test_stale_meter_response_allows_null_time() -> None:
    s = StaleMeterResponse(m_id=1, serial_number="X", last_value_time=None)
    assert s.last_value_time is None


def test_aggregate_response_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        MeasurementAggregateResponse(bucket=dt.datetime(2026, 1, 1), sum=1.0, avg=1.0)  # type: ignore[call-arg]
