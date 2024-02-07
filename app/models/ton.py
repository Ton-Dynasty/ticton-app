from email.headerregistry import Address
from typing import Literal
from pydantic import BaseModel, Field


class TonProofPayload(BaseModel):
    telegram_id: int = Field(..., description="telegram user id")


class TonProofDomain(BaseModel):
    lengthBytes: int = Field(description="AppDomain Length")
    value: str = Field(description="app domain name (as url part, without encoding)")


class TonProofMetadata(BaseModel):
    timestamp: int = Field(description="64-bit unix epoch time of the signing operation (seconds)")
    domain: TonProofDomain = Field(description="Domain name of the contract")
    signature: str = Field(description="base64-encoded signature")
    payload_hex: str = Field("", description="payload from the request", alias="payload")


class TonProofReply(BaseModel):
    name: str = Field(description="name of the contract")
    proof: TonProofMetadata = Field(description="ton proof metadata")


class TonAccount(BaseModel):
    raw_address: str = Field(description="raw address of the account", alias="address")
    chain: Literal[-239, 3] = Field(description="chain id, -239 for testnet, 3 for mainnet")
    public_key: str = Field(description="public key of the account", alias="publicKey")
    wallet_state_init: str = Field(description="initial wallet state", alias="walletStateInit")
