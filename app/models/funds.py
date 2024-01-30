from pydantic import BaseModel, Field


class Asset(BaseModel):
    address: str = Field(description="asset address, e.g. EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA")
    symbol: str = Field(description="asset symbol, e.g. USDT")
    decimals: int = Field(description="asset decimals, e.g. 6")
    balance: int = Field(description="asset balance in minimal units, e.g. 1,000,000 for 1 USDT")
