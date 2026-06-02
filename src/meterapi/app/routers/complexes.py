from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import (
    ComplexResponse,
    ConnectionResponse,
    ErrorResponse,
    MeterResponse,
)

router = APIRouter(prefix="/complexes", tags=["complexes"])

NOT_FOUND = {404: {"model": ErrorResponse}}


@router.get("", response_model=list[ComplexResponse])
def list_complexes(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[ComplexResponse]:
    return [
        ComplexResponse.model_validate(c)
        for c in repo.list_complexes(limit=limit, offset=offset)
    ]


@router.get(
    "/{c_id}/connections",
    response_model=list[ConnectionResponse],
    responses=NOT_FOUND,
)
def list_connections_for_complex(
    c_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[ConnectionResponse]:
    if repo.get_complex(c_id) is None:
        raise HTTPException(status_code=404, detail=f"complex {c_id} not found")
    return [
        ConnectionResponse.model_validate(c)
        for c in repo.list_connections_for_complex(c_id, limit=limit, offset=offset)
    ]


@router.get(
    "/{c_id}/meters",
    response_model=list[MeterResponse],
    responses=NOT_FOUND,
)
def list_meters_for_complex(
    c_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[MeterResponse]:
    if repo.get_complex(c_id) is None:
        raise HTTPException(status_code=404, detail=f"complex {c_id} not found")
    return [
        MeterResponse.model_validate(m)
        for m in repo.list_meters_for_complex(c_id, limit=limit, offset=offset)
    ]
