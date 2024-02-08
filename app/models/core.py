from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime
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
                "oracle_address": "kQCpk40ub48fvx89vSUjOTRy0vOEEZ4crOPPfLEvg88q1EeH",
            }
        }


class Alarm(BaseModel):
    telegram_id: int = Field(description="telegram user id")
    pair_id: str = Field(description="Pair id")
    oracle: str = Field(description="Address of ticton oracle")
    id: int = Field(description="Alarm id")
    created_at: datetime = Field(description="Create at")
    closed_at: Optional[datetime] = Field(None, description="Closed at")
    # Alarm metadata
    base_asset_amount: float = Field(description="Amount of base asset, in human readable format")
    quote_asset_amount: float = Field(description="Amount of quote asset, in human readable format")
    remain_scale: int = Field(description="Remain scale of position")
    base_asset_scale: int = Field(description="Base asset scale")
    quote_asset_scale: int = Field(description="Quote asset scale")
    # Status
    status: Literal["active", "danger", "closed", "emptied"] = Field("active", description="Status of position(True if active, False if inactive)")
    reward: float = Field(
        0.0,
        description="Reward of position, in human readable format. Only available if position is closed",
    )

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "pair_id": "123e4567-e89b-12d3-a456-426614174000",
                "oracle": "kQCpk40ub48fvx89vSUjOTRy0vOEEZ4crOPPfLEvg88q1EeH",
                "id": 123456789,
                "created_at": "2021-08-01T00:00:00Z",
                "synced_at": "2021-08-01T00:00:00Z",
                "base_asset_amount": 1.0,
                "quote_asset_amount": 3.3,
                "remain_scale": 1,
                "base_asset_scale": 1,
                "quote_asset_scale": 1,
                "status": "active",
                "reward": 0.0,
            }
        }


class Asset(BaseModel):
    address: str = Field(description="asset address, e.g. EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA")
    symbol: str = Field(description="asset symbol, e.g. USDT")
    decimals: int = Field(description="asset decimals, e.g. 6")
    balance: int = Field(description="asset balance in minimal units, e.g. 1,000,000 for 1 USDT")
    image: Optional[str] = Field(description="asset icon")


class PriceFeed(BaseModel):
    source: str = Field(description="price source, e.g. gateio, ticton, active")
    last_updated_at: datetime = Field(description="price timestamp")
    price: float = Field(description="price of asset in human readable format")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
