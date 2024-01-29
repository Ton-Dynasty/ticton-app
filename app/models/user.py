from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional
from app.models.primitives import ObjectId


class User(BaseModel):
    id: ObjectId = Field(alias="_id")
    telegram_id: int = Field(description="telegram user id")
    telegram_name: str = Field(description="telegram user name")
    wallet: Optional[str] = Field(description="wallet address in uesr friendly format")
    balances: Dict[str, float] = Field(
        description="user balances in different assets", default={}
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "066de609-b04a-4b30-b46c-32537c7f1f6e",
                "title": "Don Quixote",
                "author": "Miguel de Cervantes",
                "synopsis": "...",
            }
        }


class UserRegister(BaseModel):
    wallet: str = Field(description="wallet address in uesr friendly format")
    wallet_type: Literal[
        "telegram-wallet", "tonkeeper", "mytonwallet", "tonhub"
    ] = Field(..., description="wallet type")
