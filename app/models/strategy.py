from pydantic import BaseModel, Field, ConfigDict
import uuid


class StrategyModel(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(description="Strategy name")
    description: str = Field(description="Strategy description")
    provider: str = Field(description="Strategy provider")
    acc_rewards: float = Field(description="Accumulated rewards in TIC token")
    fee_rate: float = Field(
        description="Fee rate in percentage, incurs when user withdraws rewards"
    )
