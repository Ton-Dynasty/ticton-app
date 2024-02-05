from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4

from app.models.core import Pair


class Provider(BaseModel):
    """
    Provider is the model for strategy provider
    """

    id: str = Field(default_factory=lambda: uuid4().hex, description="Provider id")
    name: str = Field(description="Provider name")
    description: Optional[str] = Field(None, description="Provider description")
    acc_rewards: float = Field(
        0.0, description="Accumulated reward tokens in human readable format"
    )
    tick_amount: int = Field(0, description="Total tick counts")
    wind_amount: int = Field(0, description="Total wind counts")
    pairs: List[Pair] = Field(
        description="List of pairs that provider is providing strategy for"
    )


class UpdatePriceRequest(BaseModel):
    pair_id: str = Field(description="Pair id")
    price: float = Field(description="Price of asset in human readable format")


class PriceResponse(BaseModel):
    """
    Price is the model for price of asset
    """

    price: float = Field(description="Price of asset in human readable format")
    timestamp: datetime = Field(description="Timestamp of price")


class CreateProviderRequest(BaseModel):
    name: str = Field(description="Provider name")
    description: Optional[str] = Field(None, description="Provider description")
    pairs: List[Pair] = Field(
        description="List of pairs that provider is providing strategy for"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Ton Dynasty",
                "description": "Ton Dynasty is the official strategy provider for Tic Ton",
                "pairs": [
                    {
                        "oracle_address": "kQDIuXyeKZ9-Bxezc2UaI6Ct8megUpIYwAjCIWOKPhkMMrip",
                        "base_asset_address": "0QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACkT",
                        "quote_asset_address": "kQBqSpvo4S87mX9tjHaG4zhYZeORhVhMapBJpnMZ64jhrP-A",
                        "base_asset_symbol": "TON",
                        "quote_asset_symbol": "jUSDT",
                    },
                ],
            }
        }
