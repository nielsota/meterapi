from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app._responses import BAD_REQUEST, NOT_FOUND, VALIDATION_ERROR
from meterapi.app._time import to_utc
from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    Grain,
    MeasurementAggregateResponse,
    MeasurementResponse,
    Page,
)

router = APIRouter(prefix="/measurements", tags=["measurements"])

_FROM = Query(
    None, alias="from",
    description="ISO-8601 start (inclusive), UTC. Naive values are assumed UTC. Defaults to now-7d.",
)
_TO = Query(
    None,
    description="ISO-8601 end (exclusive), UTC. Naive values are assumed UTC. Defaults to now.",
)
_ERRORS = {**NOT_FOUND, **BAD_REQUEST, **VALIDATION_ERROR}


def _resolve_window(
    from_: datetime | None, to: datetime | None,
) -> tuple[datetime, datetime]:
    """Resolve and normalize the [from, to) window to naive-UTC for DB comparison."""
    now = datetime.now(tz=UTC)
    end = to_utc(to) if to is not None else now
    start = to_utc(from_) if from_ is not None else end - timedelta(days=7)
    if start > end:
        raise HTTPException(status_code=400, detail="from must be <= to")
    return start.replace(tzinfo=None), end.replace(tzinfo=None)


@router.get("/aggregate", response_model=list[MeasurementAggregateResponse], responses=_ERRORS)
def aggregate_measurements(
    serial_number: str = Query(..., min_length=1),
    grain: Grain = Query(...),
    from_: datetime | None = _FROM,
    to: datetime | None = _TO,
    measurement_type: str | None = Query(None),
    repo: Repository = Depends(get_repository),
) -> list[MeasurementAggregateResponse]:
    start, end = _resolve_window(from_, to)
    if not repo.meter_exists(serial_number):
        raise HTTPException(status_code=404, detail=f"meter {serial_number!r} not found")
    rows = repo.aggregate_measurements(
        serial=serial_number, grain=grain, from_=start, to=end,
        measurement_type=measurement_type,
    )
    return [MeasurementAggregateResponse.model_validate(r) for r in rows]


@router.get("", response_model=Page[MeasurementResponse], responses=_ERRORS)
def list_measurements(
    serial_number: str = Query(..., min_length=1),
    from_: datetime | None = _FROM,
    to: datetime | None = _TO,
    measurement_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[MeasurementResponse]:
    start, end = _resolve_window(from_, to)
    if not repo.meter_exists(serial_number):
        raise HTTPException(status_code=404, detail=f"meter {serial_number!r} not found")
    items = repo.list_measurements(
        serial=serial_number, from_=start, to=end,
        measurement_type=measurement_type, limit=limit, offset=offset,
    )
    total = repo.count_measurements(
        serial=serial_number, from_=start, to=end, measurement_type=measurement_type,
    )
    return Page[MeasurementResponse](
        items=[MeasurementResponse.model_validate(r) for r in items],
        total=total, limit=limit, offset=offset,
    )
