from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "postgresql+psycopg://ccn:ccn@postgres:5432/ccn"
    redis_url: str = "redis://redis:6379/0"
    api_key: str = Field(default="", alias="CCN_API_KEY")
    enable_api_docs: bool = False
    auth_fail_limit_per_minute: int = 10
    read_limit_per_minute: int = 120
    write_limit_per_minute: int = 30

@lru_cache
def get_settings() -> Settings:
    return Settings()
