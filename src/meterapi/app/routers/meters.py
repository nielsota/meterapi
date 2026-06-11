from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app._responses import NOT_FOUND, VALIDATION_ERROR
from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    LastReading,
    MeterDetailResponse,
    MeterResponse,
    Page,
    StaleMeterResponse,
)

router = APIRouter(prefix="/meters", tags=["meters"])


@router.get(
    "/stale",
    response_model=Page[StaleMeterResponse],
    responses=VALIDATION_ERROR,
)
def list_stale_meters(
    hours: int = Query(24, gt=0, le=8760, description="Staleness window in hours (max 8760 = 1 year)."),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[StaleMeterResponse]:
    rows = repo.list_stale_meters(hours=hours, limit=limit, offset=offset)
    return Page[StaleMeterResponse](
        items=[StaleMeterResponse.model_validate(r) for r in rows],
        total=repo.count_stale_meters(hours=hours),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{serial_number}",
    response_model=MeterDetailResponse,
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def get_meter_by_serial(
    serial_number: str,
    repo: Repository = Depends(get_repository),
) -> MeterDetailResponse:
    detail = repo.get_meter_by_serial(serial_number)
    if detail is None:
        raise HTTPException(
            status_code=404, detail=f"meter {serial_number!r} not found"
        )
    last = (
        LastReading.model_validate(detail.last_reading)
        if detail.last_reading is not None
        else None
    )
    return MeterDetailResponse(
        **MeterResponse.model_validate(detail.meter).model_dump(),
        installation_goal=detail.installation_location,
        room_label=detail.room_label,
        last_reading=last,
    )
