from pydantic import BaseModel, Field

class MeterLastValueResponse(BaseModel):
    type: str | None = None
    serial: str | None = None
    room: str | None = None
    value: float | None = None
    unit: str | None = None


class MeterLastValueRequest(BaseModel):
    connection_id: int = Field(..., alias="connectionId", description="connection.c_id")
    meter_type: str = Field(..., alias="meterType", description="installation_location.goal — e.g. WKV, WARM, KOUD")
