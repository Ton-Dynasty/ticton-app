from pydantic import BaseModel, Field


class LeaderBoardRecord(BaseModel):
    user_id: int = Field(description="telegram user id")
    name: str = Field(description="user name")
    wallet: str = Field(description="wallet address in uesr friendly format")
    rewards: float = Field(description="total rewards in TIC token")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "name": "John Doe",
                "wallet": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "rewards": 1000,
            }
        }
