import json

import boto3
import pytest
from moto import mock_aws
from pydantic import ValidationError

from meterapi.config import Settings
from meterapi.db import ConfigurationError, _resolve_credentials
from meterapi.models import DBCredentials


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip any DB_/AWS_ env vars so _clean_settings() / boto3 see a clean process env."""
    for var in (
        "DB_SECRET_ARN", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT",
        "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN", "AWS_PROFILE",
    ):
        monkeypatch.delenv(var, raising=False)


def _clean_settings(**kwargs: object) -> Settings:
    """Construct Settings without loading the project's .env."""
    return Settings(_env_file=None, **kwargs)  # type: ignore[arg-type]


@mock_aws
def test_credentials_from_secrets_manager() -> None:
    client = boto3.client("secretsmanager", region_name="eu-central-1")
    arn = client.create_secret(
        Name="db",
        SecretString=json.dumps(
            {"username": "u", "password": "p", "host": "h", "dbname": "d", "port": 5432}
        ),
    )["ARN"]
    creds = _resolve_credentials(_clean_settings(db_secret_arn=arn, aws_region="eu-central-1"))
    assert (creds.user, creds.host, creds.database, creds.port) == ("u", "h", "d", 5432)


def test_credentials_from_env_vars() -> None:
    creds = _resolve_credentials(
        _clean_settings(db_host="h", db_user="u", db_password="p", db_name="d", db_port=6543)
    )
    assert (creds.user, creds.host, creds.database, creds.port) == ("u", "h", "d", 6543)


def test_credentials_no_config_raises() -> None:
    with pytest.raises(ConfigurationError, match="No DB credentials"):
        _resolve_credentials(_clean_settings())


def test_settings_is_frozen() -> None:
    s = _clean_settings()
    with pytest.raises(ValidationError):
        s.db_port = 1


def test_dbcredentials_is_frozen() -> None:
    c = DBCredentials(user="u", password="p", host="h", database="d")
    with pytest.raises(ValidationError):
        c.host = "x"
