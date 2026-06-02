from fastapi import APIRouter, Depends, HTTPException, Query

from meterapi.app.dependencies import get_repository
from meterapi.db import Repository
from meterapi.models.api import ErrorResponse, RoomResponse

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get(
    "/{c_id}/rooms",
    response_model=list[RoomResponse],
    responses={404: {"model": ErrorResponse}},
)
def list_rooms_for_connection(
    c_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: Repository = Depends(get_repository),
) -> list[RoomResponse]:
    if repo.get_connection(c_id) is None:
        raise HTTPException(status_code=404, detail=f"connection {c_id} not found")
    return [
        RoomResponse.model_validate(r)
        for r in repo.list_rooms_for_connection(c_id, limit=limit, offset=offset)
    ]
