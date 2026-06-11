import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from meterapi.app.errors import register_error_handlers
from meterapi.app.routers import (
    complexes,
    connections,
    health,
    measurements,
    meters,
    security,
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


app = FastAPI(title="Meters API", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)

api_v1 = APIRouter(prefix="/v1")
for r in (complexes, connections, meters, measurements):
    api_v1.include_router(r.router)
app.include_router(api_v1)

# Unversioned: infra probes and the (auth) token stub (see WORK-001).
app.include_router(health.router)
app.include_router(security.router)
