import json
from collections.abc import Iterator

import boto3
from fastapi import Request
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from meterapi.config import Settings
from meterapi.models import DBCredentials


class MeterApiError(Exception):
    """Base class for all domain errors in meterapi."""


class ConfigurationError(MeterApiError):
    """Raised when configuration / credentials cannot be resolved."""


def _resolve_credentials(settings: Settings) -> DBCredentials:
    """Resolve DB credentials from .env or secret manager"""
    env_fields = (settings.db_host, settings.db_user, settings.db_password)
    if all(env_fields):
        return DBCredentials(
            user=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            database=settings.db_name,
            port=settings.db_port,
        )

    if not settings.db_secret_arn:
        raise ConfigurationError(
            "No DB credentials configured: set DB_HOST/DB_USER/DB_PASSWORD or DB_SECRET_ARN."
        )

    arn = settings.db_secret_arn
    try:
        client = boto3.client("secretsmanager", region_name=settings.aws_region)
        resp = client.get_secret_value(SecretId=arn)
        payload = json.loads(resp["SecretString"])
        return DBCredentials.model_validate(payload)
    except Exception as exc:
        raise ConfigurationError(exc) from exc


def create_engine_from_settings(settings: Settings) -> Engine:
    c = _resolve_credentials(settings)
    url = (
        f"postgresql+psycopg://{c.user}:{c.password}@{c.host}:{c.port}/{c.database}"
        "?sslmode=require"
    )
    return create_engine(url, pool_size=5, max_overflow=5, pool_pre_ping=True)


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
