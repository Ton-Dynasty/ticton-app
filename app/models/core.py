from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from app.models.funds import Asset


class Position(BaseModel):
    telegram_id: int = Field(description="telegram user id")
    base_asset: str = Field(description="Address of base asset")
    quote_asset: str = Field(description="Address of quote asset")
    base_amount: float = Field(description="Amount of base asset")
    quote_amount: float = Field(description="Amount of quote asset")
    oracle: str = Field(description="Address of oracle")
    price: float = Field(description="Price of quote asset per base asset")
    provider: str = Field(description="Stratagy provider")
    status: bool = Field(
        description="Status of position(True if active, False if inactive)"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "base_asset": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "quote_asset": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "base_amount": 1,
                "quote_amount": 1,
                "oracle": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "price": 1,
                "provider": "Ton Dynasty",
                "status": True,
            }
        }


class CreatePositionRequest(BaseModel):
    base_asset: str = Field(description="Address of base asset")
    quote_asset: str = Field(description="Address of quote asset")
    base_amount: float = Field(description="Amount of base asset")
    quote_amount: float = Field(description="Amount of quote asset")
    oracle: str = Field(description="Address of oracle")
    price: float = Field(description="Price of quote asset per base asset")
    provider: str = Field(description="Stratagy provider")
    status: bool = Field(
        description="Status of position(True if active, False if inactive)"
    )
