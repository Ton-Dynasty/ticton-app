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
    base_asset_image_url: Optional[str] = Field(default=None, description="Image url of base asset")
    quote_asset_image_url: Optional[str] = Field(default=None, description="Image url of quote asset")


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
    id: int = Field(description="Alarm id")
    pair_id: str = Field(description="Pair id")
    oracle: str = Field(description="Address of ticton oracle")
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
    reward: float = Field(0.0, description="Reward of position, in human readable format. Only available if position is closed")

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
    image_url: Optional[str] = Field(default=None, description="icon of exchange / price feed")
    source: str = Field(description="price source, e.g. gateio, ticton, active", examples=["gateio", "ticton", "binance"])
    last_updated_at: datetime = Field(description="price timestamp")
    price: float = Field(description="price of asset in human readable format", examples=[2.2])
    symbol: str = Field(description="symbol of the pair", examples=["TON/USDT"])

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}



class AlarmResponse(BaseModel):
    base_asset_image_url: str = Field(description="Image url of base asset")
    quote_asset_image_url: str = Field(description="Image url of quote asset")
    created_since: str = Field(description="Created since", examples=["10 mins ago"])
    price: float = Field(description="Price", examples=[2.735])
    base_asset_scale: int = Field(description="Base asset scale", examples=[1])
    quote_asset_scale: int = Field(description="Quote asset scale", examples=[1])
    reward_amount: float = Field(description="Reward amount", examples=[2.26])
    base_asset_threshold: float = Field(description="Base asset threshold, for example, if the value is 0.3 means 1 Unit equals to 0.3 base_asset", examples=[0.3])
    arbitrage_ratio: float = Field(default=0.0, description="remain scale / original scale", examples=[0.5])
    watchmaker: str = Field(description="Address of watch maker")
    alarm_id: int = Field(description="Alarm id", examples=[13])
    alarm_address: str = Field(description="Address of alarm")
    remain_scale: int = Field(description="Remain scale of position", examples=[1])

