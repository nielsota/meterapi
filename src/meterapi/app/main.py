import logging

from fastapi import Depends, FastAPI
from sqlmodel import Session

from meterapi.models import MeterLastValue, RequestParams, get_session
from meterapi.services.dbservice import MeterRepository


def get_meter_repository(
    session: Session = Depends(get_session),
) -> MeterRepository:
    return MeterRepository(session)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meters API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/meters/last-values", response_model=list[MeterLastValue])
def last_values(
    params: RequestParams = Depends(),
    repository: MeterRepository = Depends(get_meter_repository),
) -> list[MeterLastValue]:
    values = repository.get_last_meter_values(
        connection_id=params.connection_id,
        meter_type=params.meter_type,
    )
    logger.info(
        "Returned %d last values for connection %d, type %s",
        len(values), params.connection_id, params.meter_type,
    )
    return values
