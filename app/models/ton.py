from pydantic import BaseModel, Field


class TonProofPayload(BaseModel):
    telegram_id: int = Field(..., description="telegram user id")


class TonProofDomain(BaseModel):
    lengthBytes: int = Field(description="AppDomain Length")
    value: str = Field(description="app domain name (as url part, without encoding)")


class TonProofMetadata(BaseModel):
    timestamp: str = Field(description="64-bit unix epoch time of the signing operation (seconds)")
    domain: TonProofDomain = Field(description="Domain name of the contract")
    signature: str = Field(description="base64-encoded signature")
    payload: str = Field(description="payload from the request")


class TonProofReply(BaseModel):
    name: str = Field(description="name of the contract")
    proof: TonProofMetadata = Field(description="ton proof metadata")
