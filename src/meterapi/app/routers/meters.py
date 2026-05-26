from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    ErrorResponse,
    LastReading,
    MeterDetailResponse,
    StaleMeterResponse,
)

router = APIRouter(prefix="/meters", tags=["meters"])


@router.get(
    "/stale",
    response_model=list[StaleMeterResponse],
)
def list_stale_meters(
    hours: int = Query(24, gt=0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[StaleMeterResponse]:
    rows = repo.list_stale_meters(hours=hours, limit=limit, offset=offset)
    return [
        StaleMeterResponse(
            m_id=r.m_id,
            serial_number=r.serial_number,
            last_value_time=r.last_value_time,
        )
        for r in rows
    ]


@router.get(
    "/{serial}",
    response_model=MeterDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_meter_by_serial(
    serial: str,
    repo: Repository = Depends(get_repository),
) -> MeterDetailResponse:
    detail = repo.get_meter_by_serial(serial)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"meter {serial!r} not found")
    last = (
        LastReading(
            value=detail.last_reading.value,
            unit=detail.last_reading.unit,
            value_time=detail.last_reading.value_time,
            measurement_type=detail.last_reading.measurement_type,
        )
        if detail.last_reading is not None
        else None
    )
    m = detail.meter
    return MeterDetailResponse(
        m_id=m.m_id,
        serial_number=m.serial_number,
        communication_protocol=m.communication_protocol,
        offset=m.offset,
        scale=m.scale,
        due_date_month=m.due_date_month,
        installation_location=detail.installation_location,
        room=detail.room_label,
        last_reading=last,
    )
