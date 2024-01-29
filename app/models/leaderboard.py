from pydantic import BaseModel, Field, ConfigDict


class LeaderBoardRecord(BaseModel):
    user_id: int = Field(description="telegram user id")
    name: str = Field(description="user name")
    wallet: str = Field(description="wallet address in uesr friendly format")
    rewards: float = Field(description="total rewards in TIC token")
