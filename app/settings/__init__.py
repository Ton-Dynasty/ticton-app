from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    TICTON_DB_HOST: str
    TICTON_DB_PORT: int
    TICTON_DB_USERNAME: str
    TICTON_DB_PASSWORD: str
    TICTON_DB_NAME: str
    TICTON_REDIS_HOST: str
    TICTON_REDIS_PORT: int
    TICTON_REDIS_PASSWORD: str
    TICTON_REDIS_DB: int
    TICTON_TG_BOT_TOKEN: str
    TICTON_MANIFEST_URL: str
    TICTON_MODE: Literal["dev", "main"]


@lru_cache()
def get_settings():
    return Settings()  # type: ignore
