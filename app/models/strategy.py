from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StrategyPairs(BaseModel):
    base_asset: str = Field(description="base asset address")
    quote_asset: str = Field(description="quote asset address")


class Strategy(BaseModel):
    name: str = Field(description="Strategy name")
    description: str = Field(description="Strategy description")
    provider: str = Field(description="Strategy provider")
    acc_rewards: float = Field(description="Accumulated rewards in TIC token")
    fee_rate: float = Field(0, description="Fee rate in percentage, incurs when user withdraws rewards")
    pairs: Optional[List[StrategyPairs]] = Field(None, description="Strategy pairs")


class Price(BaseModel):
    provider: str = Field(description="price provider")
    base_asset_address: str = Field(description="base asset address")
    base_asset_symbol: str = Field(description="base asset symbol")
    quote_asset_address: str = Field(description="quote asset address")
    quote_asset_symbol: str = Field(description="quote asset symbol")
    price: float = Field(description="relative price of quote asset to base asset, e.g. 2.5 for 2.5 USDT per TON")
    updated_at: datetime = Field(description="price updated time in RFC3339 format")
