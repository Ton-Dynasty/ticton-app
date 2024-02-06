from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class User(BaseModel):
    telegram_id: int = Field(description="telegram user id")
    telegram_name: str = Field(description="telegram user name")
    avatar: Optional[str] = Field(None, description="user avatar")
    wallet: str = Field(description="wallet address in uesr friendly format")
    total_rewards: float = Field(0.0, description="total rewards of user")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "telegram_name": "John Doe",
                "wallet": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "balances": [{"address": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA", "symbol": "USDT", "decimals": 6, "balance": 1000000}],
            }
        }


class IUser(BaseModel):
    telegram_id: int = Field(description="telegram user id")
    telegram_name: str = Field(description="telegram user name")
    wallet: str = Field(None, description="wallet address in uesr friendly format")


class UserRegisterRequest(BaseModel):
    wallet_type: Literal["telegram-wallet", "tonkeeper", "mytonwallet", "tonhub"] = Field(..., description="wallet type")


class WithdrawReqeuest(BaseModel):
    amount: float = Field(..., description="amount to withdraw")
    asset: str = Field(..., description="asset to withdraw")
    wallet: Optional[str] = Field(None, description="wallet address to withdraw, if not specified, user's wallet will be used")
