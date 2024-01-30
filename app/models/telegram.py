from pydantic import BaseModel, Field
from typing import Optional


class TelegramUser(BaseModel):
    allows_write_to_pm: Optional[bool] = Field(None, alias="allows_write_to_pm")
    first_name: str = Field(alias="first_name")
    id: int = Field(alias="id")
    is_premium: Optional[bool] = Field(None, alias="is_premium")
    language_code: str = Field(alias="language_code")
    last_name: str = Field(alias="last_name")
    username: str = Field(alias="username")
