from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    TICTON_DB_HOST: str
    TICTON_DB_PORT: int
    TICTON_DB_USERNAME: str
    TICTON_DB_PASSWORD: str
    TICTON_DB_NAME: str
    TICTON_TG_BOT_TOKEN: str
    TICTON_MANIFEST_URL: str


@lru_cache()
def get_settings():
    return Settings()  # type: ignore
