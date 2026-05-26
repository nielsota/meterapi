from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    Grain,
    MeasurementAggregateResponse,
    MeasurementResponse,
)

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("/aggregate", response_model=list[MeasurementAggregateResponse])
def aggregate_measurements(
    serial: str = Query(...),
    grain: Grain = Query(...),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    measurement_type: str | None = Query(None),
    repo: Repository = Depends(get_repository),
) -> list[MeasurementAggregateResponse]:
    now = datetime.now(tz=UTC)
    end = to or now
    start = from_ or (end - timedelta(days=7))
    if start > end:
        raise HTTPException(status_code=400, detail="from must be <= to")
    rows = repo.aggregate_measurements(
        serial=serial, grain=grain, from_=start, to=end,
        measurement_type=measurement_type,
    )
    return [
        MeasurementAggregateResponse(
            bucket=r.bucket, sum=r.sum, avg=r.avg, count=r.count,
        )
        for r in rows
    ]


@router.get("", response_model=list[MeasurementResponse])
def list_measurements(
    serial: str = Query(...),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    measurement_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[MeasurementResponse]:
    now = datetime.now(tz=UTC)
    end = to or now
    start = from_ or (end - timedelta(days=7))
    if start > end:
        raise HTTPException(status_code=400, detail="from must be <= to")
    rows = repo.list_measurements(
        serial=serial, from_=start, to=end,
        measurement_type=measurement_type,
        limit=limit, offset=offset,
    )
    return [MeasurementResponse.model_validate(r) for r in rows]
