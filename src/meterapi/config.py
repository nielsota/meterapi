from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    aws_region: str = "eu-central-1"
    db_secret_arn: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
