from pydantic import BaseModel, Field


class TonProofPayload(BaseModel):
    telegram_id: int = Field(..., description="telegram user id")
    expire_at: int = Field(..., description="expiration timestamp")
