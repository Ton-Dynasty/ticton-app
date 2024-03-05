from pydantic import BaseModel, Field


class LeaderBoardRecord(BaseModel):
    rank: int = Field(description="user rank based on rewards")
    name: str = Field(description="user name")
    rewards: float = Field(description="total rewards in TIC token")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "rank": 1,
                "user_id": 123456789,
                "name": "John Doe",
                "wallet": "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA",
                "rewards": 1000,
            }
        }
