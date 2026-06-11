from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app._responses import NOT_FOUND, VALIDATION_ERROR
from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import Page, RoomResponse

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get(
    "/{connection_id}/rooms",
    response_model=Page[RoomResponse],
    responses={**NOT_FOUND, **VALIDATION_ERROR},
)
def list_rooms_for_connection(
    connection_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> Page[RoomResponse]:
    if repo.get_connection(connection_id) is None:
        raise HTTPException(
            status_code=404, detail=f"connection {connection_id} not found"
        )
    items = repo.list_rooms_for_connection(connection_id, limit=limit, offset=offset)
    return Page[RoomResponse](
        items=[RoomResponse.model_validate(r) for r in items],
        total=repo.count_rooms_for_connection(connection_id),
        limit=limit,
        offset=offset,
    )
