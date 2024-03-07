from pydantic import BaseModel, Field
from typing import List
from pytoncenter.v3.models import AddressLike


class LeaderboardRecordResponse(BaseModel):
    address: str = Field(description="Address of user")
    rank: int = Field(description="Rank of user")
    reward: float = Field(description="Reward of user", examples=[2.26])


class LeaderboardRecord(LeaderboardRecordResponse):
    is_current_user: bool = Field(default=False, description="Is current record belong to user", examples=[True])
    


class LeaderboardResponse(BaseModel):
    current_address: str = Field(description="Address of current user", examples=["0QC8zFHM8LCMp9Xs--w3g9wmf7RwuDgJcQtV-oHZRSCqQXmw"])
    curent_reward_amount: float = Field(description="Reward amount for current user", examples=[2.26])
    current_rank: int = Field(description="Current rank", examples=[239])
    leaderboard: List[LeaderboardRecordResponse] = Field(description="Leaderboard records")
