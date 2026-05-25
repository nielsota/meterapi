import json
from functools import lru_cache

import boto3
from sqlmodel import Session, create_engine

from meterapi.config import get_settings
from meterapi.models import DBCredentials


@lru_cache(maxsize=1)
def _credentials() -> DBCredentials:
    settings = get_settings()

    if settings.db_host and settings.db_user and settings.db_password:
        return DBCredentials(
            user=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            database=settings.db_name,
            port=settings.db_port,
        )

    if not settings.db_secret_arn:
        raise RuntimeError(
            "No DB credentials configured: set DB_HOST/DB_USER/DB_PASSWORD or DB_SECRET_ARN"
        )

    client = boto3.client("secretsmanager", region_name=settings.aws_region)
    resp = client.get_secret_value(SecretId=settings.db_secret_arn)
    return DBCredentials.model_validate(json.loads(resp["SecretString"]))


@lru_cache(maxsize=1)
def get_engine():
    c = _credentials()
    url = f"postgresql+psycopg://{c.user}:{c.password}@{c.host}:{c.port}/{c.database}?sslmode=require"
    return create_engine(url, pool_size=5, max_overflow=5, pool_pre_ping=True)


def get_session():
    with Session(get_engine()) as session:
        yield session
