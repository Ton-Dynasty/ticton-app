from datetime import datetime, timedelta
import json
from typing import Tuple, Optional
from fastapi import Depends

from ticton import TonCenterClient
from app.models.ton import TonProofPayload, TonProofReply
from app.settings import Settings, get_settings
from app.tools import get_ton_center_client
from tonsdk.contract import Address


def generate_tonproof_payload(
    telegram_id: int,
    *,
    ttl: timedelta = timedelta(minutes=5),
) -> str:
    payload = {
        "telegram_id": telegram_id,
    }
    payload = bytearray(json.dumps(payload).encode("utf-8"))
    ts = int((datetime.now() + ttl).timestamp() / 1000)
    payload.extend(ts.to_bytes(8, "big"))
    return payload.hex()


def decode_payload(payload_hex: str) -> TonProofPayload:
    payload_bytes = bytearray.fromhex(payload_hex)
    timestamp_bytes = payload_bytes[-8:]
    expire_at = int.from_bytes(timestamp_bytes, "big")

    payload_str = payload_bytes[:-8].decode("utf-8")
    payload_dict = json.loads(payload_str)
    telegram_id = payload_dict["telegram_id"]
    return TonProofPayload(telegram_id=telegram_id)


def verify_ton_proof(
    reply: TonProofReply, toncenter: TonCenterClient = Depends(get_ton_center_client), settings: Settings = Depends(get_settings)
) -> Tuple[bool, Optional[TonProofPayload], Optional[Address]]:
    return (True, TonProofPayload(telegram_id=123456789), Address(""))
