from pydantic import BaseModel, Field
from typing import List
from pytoncenter.v3.models import AddressLike


class LeaderboardRecord(BaseModel):
    address: str = Field(description="Address of user", examples=["0:29754304394b879c1a3e45275b8a4919677a9622d64b7578f27dff6537f792e5"])
    reward: float = Field(description="Reward of user", examples=[2.26])


class LeaderboardRecordResponse(LeaderboardRecord):
    is_current_user: bool = Field(default=False, description="Is current record belong to user", examples=[True])
    rank: int = Field(description="Rank of user")


class LeaderboardRecordList(BaseModel):
    leaderboard: List[LeaderboardRecord] = Field(description="Leaderboard records")


class LeaderboardResponse(BaseModel):
    current_address: str = Field(description="Address of current user", examples=["0:29754304394b879c1a3e45275b8a4919677a9622d64b7578f27dff6537f792e5"])
    current_reward: float = Field(description="Reward amount for current user", examples=[2.26])
    current_rank: int = Field(description="Current rank", examples=[239])
    leaderboard: List[LeaderboardRecordResponse] = Field(description="Leaderboard records")
