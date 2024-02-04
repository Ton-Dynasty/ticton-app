from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from app.models.funds import Asset
import uuid


class Pair(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, description="Pair id")
    oracle_address: str = Field(description="Address of ticton oracle")
    base_asset_address: str = Field(description="Address of base asset")
    quote_asset_address: str = Field(description="Address of quote asset")
    base_asset_symbol: str = Field(description="Symbol of base asset")
    quote_asset_symbol: str = Field(description="Symbol of quote asset")
    base_asset_decimals: int = Field(description="Decimals of base asset")
    quote_asset_decimals: int = Field(description="Decimals of quote asset")


class CreatePairRequest(BaseModel):
    oracle_address: str = Field(description="Address of ticton oracle")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "oracle_address": "kQDIuXyeKZ9-Bxezc2UaI6Ct8megUpIYwAjCIWOKPhkMMrip",
            }
        }


class Position(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, description="Position id")
    telegram_id: int = Field(description="telegram user id")
    pair_id: str = Field(description="Pair id")
    base_asset_amount: float = Field(
        description="Amount of base asset, in human readable format"
    )
    quote_asset_amount: float = Field(
        description="Amount of quote asset, in human readable format"
    )
    provider_id: str = Field(description="Stratagy provider")
    status: Literal["active", "danger", "closed"] = Field(
        "active", description="Status of position(True if active, False if inactive)"
    )
    reward: Optional[float] = Field(
        None,
        description="Reward of position, in human readable format. Only available if position is closed",
    )

    class Config:
        populate_by_name = True


class CreatePositionRequest(BaseModel):
    """CreatePositionRequest is for Tick"""

    telegram_id: int = Field(description="telegram user id")
    pair_id: str = Field(description="Pair id")
    base_asset_amount: float = Field(
        description="Amount of base asset, in human readable format"
    )
    quote_asset_amount: float = Field(
        description="Amount of quote asset, in human readable format"
    )
    provider_id: str = Field(description="Stratagy provider")
