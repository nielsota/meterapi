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
    Page,
    RoomResponse,
    StaleMeterResponse,
)


def test_complex_response_maps_pk_to_id_and_date() -> None:
    c = Complex(c_id=1, due_date="2026-01-01", name="A")
    resp = ComplexResponse.model_validate(c)
    assert resp.id == 1
    assert resp.due_date == dt.date(2026, 1, 1)


def test_complex_response_serializes_camel_case() -> None:
    c = Complex(c_id=1, due_date="2026-01-01", name="A")
    dumped = ComplexResponse.model_validate(c).model_dump(by_alias=True)
    assert dumped["id"] == 1
    assert dumped["dueDate"] == dt.date(2026, 1, 1)
    assert "c_id" not in dumped and "due_date" not in dumped


def test_connection_response_id_and_fk() -> None:
    c = Connection(c_id=10, complex_id=1, street="X", house_number=2, zip_code="1", town="T")
    dumped = ConnectionResponse.model_validate(c).model_dump(by_alias=True)
    assert dumped["id"] == 10
    assert dumped["complexId"] == 1
    assert dumped["houseNumber"] == 2


def test_room_response_id_and_fk() -> None:
    r = Room(r_id=1, connection_id=10, name="k", number_of_room=1)
    dumped = RoomResponse.model_validate(r).model_dump(by_alias=True)
    assert dumped["id"] == 1
    assert dumped["connectionId"] == 10
    assert dumped["numberOfRoom"] == 1


def test_meter_response_renames_offset_and_camel() -> None:
    m = Meter(
        m_id=5, serial_number="SN",
        communication_protocol=MeterCommunicationProtocol.LORA,
        offset=2.5, scale=1.0,
    )
    resp = MeterResponse.model_validate(m)
    assert resp.id == 5
    assert resp.calibration_offset == 2.5
    dumped = resp.model_dump(by_alias=True)
    assert dumped["serialNumber"] == "SN"
    assert dumped["calibrationOffset"] == 2.5
    assert "offset" not in dumped and "m_id" not in dumped


def test_meter_detail_renamed_fields() -> None:
    m = Meter(m_id=5, serial_number="SN", communication_protocol=MeterCommunicationProtocol.LORA)
    detail = MeterDetailResponse(
        **MeterResponse.model_validate(m).model_dump(),
        installation_goal="WKV",
        room_label="kitchen_1",
        last_reading=LastReading(
            value=1.0, unit="kWh",
            value_time=dt.datetime(2026, 1, 1), measurement_type="energy",
        ),
    )
    dumped = detail.model_dump(by_alias=True)
    assert dumped["installationGoal"] == "WKV"
    assert dumped["roomLabel"] == "kitchen_1"
    assert dumped["lastReading"]["measurementType"] == "energy"


def test_stale_meter_response_maps_pk_and_allows_null_time() -> None:
    s = StaleMeterResponse.model_validate(
        {"m_id": 1, "serial_number": "X", "last_value_time": None}
    )
    assert s.id == 1
    assert s.last_value_time is None
    assert s.model_dump(by_alias=True)["lastValueTime"] is None


def test_page_envelope_serializes() -> None:
    c = Complex(c_id=1, due_date="2026-01-01", name="A")
    page = Page[ComplexResponse](
        items=[ComplexResponse.model_validate(c)], total=3, limit=2, offset=0,
    )
    dumped = page.model_dump(by_alias=True)
    assert dumped["total"] == 3 and dumped["limit"] == 2 and dumped["offset"] == 0
    assert dumped["items"][0]["id"] == 1


def test_aggregate_response_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        MeasurementAggregateResponse(bucket=dt.datetime(2026, 1, 1), sum=1.0, avg=1.0)  # type: ignore[call-arg]
