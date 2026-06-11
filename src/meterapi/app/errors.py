"""Global exception handlers mapping domain/DB errors to sanitized HTTP responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from meterapi.db import ConfigurationError, MeterApiError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OperationalError)
    async def _operational_error(_: Request, exc: OperationalError) -> JSONResponse:
        logger.exception("database unreachable")
        return JSONResponse(status_code=503, content={"detail": "db_unreachable"})

    @app.exception_handler(ConfigurationError)
    async def _configuration_error(_: Request, exc: ConfigurationError) -> JSONResponse:
        logger.exception("configuration error")
        return JSONResponse(status_code=503, content={"detail": "db_unreachable"})

    @app.exception_handler(MeterApiError)
    async def _domain_error(_: Request, exc: MeterApiError) -> JSONResponse:
        logger.exception("domain error")
        return JSONResponse(status_code=500, content={"detail": "internal_error"})
