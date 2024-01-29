from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    allows_write_to_pm: bool = Field(..., alias="allows_write_to_pm")
    first_name: str = Field(..., alias="first_name")
    id: int = Field(..., alias="id")
    is_premium: bool = Field(..., alias="is_premium")
    language_code: str = Field(..., alias="language_code")
    last_name: str = Field(..., alias="last_name")
    username: str = Field(..., alias="username")
