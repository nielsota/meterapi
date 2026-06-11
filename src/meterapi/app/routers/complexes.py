from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app._responses import NOT_FOUND, VALIDATION_ERROR
from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    ComplexResponse,
    ConnectionResponse,
    MeterResponse,
    Page,
)

router = APIRouter(prefix="/complexes", tags=["complexes"])

_LIST_AND_NOT_FOUND = {**NOT_FOUND, **VALIDATION_ERROR}


@router.get("", response_model=Page[ComplexResponse], responses=VALIDATION_ERROR)
def list_complexes(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[ComplexResponse]:
    items = repo.list_complexes(limit=limit, offset=offset)
    return Page[ComplexResponse](
        items=[ComplexResponse.model_validate(c) for c in items],
        total=repo.count_complexes(),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{complex_id}/connections",
    response_model=Page[ConnectionResponse],
    responses=_LIST_AND_NOT_FOUND,
)
def list_connections_for_complex(
    complex_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[ConnectionResponse]:
    if repo.get_complex(complex_id) is None:
        raise HTTPException(status_code=404, detail=f"complex {complex_id} not found")
    items = repo.list_connections_for_complex(complex_id, limit=limit, offset=offset)
    return Page[ConnectionResponse](
        items=[ConnectionResponse.model_validate(c) for c in items],
        total=repo.count_connections_for_complex(complex_id),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{complex_id}/meters",
    response_model=Page[MeterResponse],
    responses=_LIST_AND_NOT_FOUND,
)
def list_meters_for_complex(
    complex_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[MeterResponse]:
    if repo.get_complex(complex_id) is None:
        raise HTTPException(status_code=404, detail=f"complex {complex_id} not found")
    items = repo.list_meters_for_complex(complex_id, limit=limit, offset=offset)
    return Page[MeterResponse](
        items=[MeterResponse.model_validate(m) for m in items],
        total=repo.count_meters_for_complex(complex_id),
        limit=limit,
        offset=offset,
    )
