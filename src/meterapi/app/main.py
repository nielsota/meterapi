import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from meterapi.app.routers import (
    complexes,
    connections,
    health,
    measurements,
    meters,
)
from meterapi.config import Settings
from meterapi.db import create_engine_from_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    app.state.settings = settings
    app.state.engine = create_engine_from_settings(settings)
    try:
        yield
    finally:
        app.state.engine.dispose()


app = FastAPI(title="Meters API", lifespan=lifespan)

for r in (health, complexes, connections, meters, measurements):
    app.include_router(r.router)
