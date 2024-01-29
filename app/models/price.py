from pydantic import BaseModel, Field, ConfigDict


class Price(BaseModel):
    provider: str = Field(description="price provider")
    price: float = Field(description="relative price of quote asset to base asset")
