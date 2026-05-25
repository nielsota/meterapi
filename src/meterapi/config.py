from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "eu-central-1"

    db_secret_arn: str | None = None

    db_host: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_name: str = "postgres"
    db_port: int = 5432


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
