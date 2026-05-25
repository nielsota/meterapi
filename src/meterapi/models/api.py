from fastapi import Query
from pydantic import BaseModel


class MeterLastValue(BaseModel):
    type: str | None = None
    serial: str | None = None
    room: str | None = None
    value: float | None = None
    unit: str | None = None


class RequestParams(BaseModel):
    """Query parameters for /meters/last-values, bundled so helpers receive one object."""
    connection_id: int = Query(..., alias="connectionId", description="connection.c_id")
    meter_type: str = Query(..., alias="meterType", description="installation_location.goal — e.g. WKV, WARM, KOUD")

    model_config = {"populate_by_name": True}
