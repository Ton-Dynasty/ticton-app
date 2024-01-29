from datetime import datetime
import json
from pytonconnect.parsers import WalletInfo
from typing import Tuple, Optional
from app.models.ton import TonProofPayload


def generate_tonproof_payload(
    telegram_id: int,
    ttl: int = 600,
) -> str:
    payload = {
        "telegram_id": telegram_id,
    }
    payload = bytearray(json.dumps(payload).encode("utf-8"))
    ts = int(datetime.now().timestamp()) + ttl
    payload.extend(ts.to_bytes(8, "big"))
    return payload.hex()


def decode_payload(payload_hex: str) -> TonProofPayload:
    payload_bytes = bytearray.fromhex(payload_hex)
    timestamp_bytes = payload_bytes[-8:]
    expire_at = int.from_bytes(timestamp_bytes, "big")

    payload_str = payload_bytes[:-8].decode("utf-8")
    payload_dict = json.loads(payload_str)
    telegram_id = payload_dict["telegram_id"]
    return TonProofPayload(telegram_id=telegram_id, expire_at=expire_at)


def verify_tonproof_payload(
    payload_hex: str, wallet_info: WalletInfo
) -> Tuple[bool, Optional[TonProofPayload]]:
    if not wallet_info.check_proof(payload_hex):
        return False, None
    payload = decode_payload(payload_hex)
    if datetime.now().timestamp() > payload.expire_at:
        return False, None
    return True, payload
