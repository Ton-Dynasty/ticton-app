from datetime import datetime, timedelta
import json
from typing import Tuple, Optional
from fastapi import Depends
from ticton import TonCenterClient
from app.models.ton import TonAccount, TonProofPayload, TonProofReply
from app.settings import Settings, get_settings
from app.tools import get_ton_center_client
from tonsdk.contract import Address
import hashlib
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder


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
    reply: TonProofReply,
    ton_account: TonAccount,
) -> Tuple[bool, Optional[TonProofPayload], Optional[Address]]:
    wc, whash = ton_account.raw_address.split(":", maxsplit=2)

    message = bytearray()
    message.extend("ton-proof-item-v2/".encode())
    message.extend(int(wc, 10).to_bytes(4, "little"))
    message.extend(bytes.fromhex(whash))
    message.extend(reply.proof.domain.lengthBytes.to_bytes(4, "little"))
    message.extend(reply.proof.domain.value.encode())
    message.extend(reply.proof.timestamp.to_bytes(8, "little"))
    message.extend(bytes.fromhex(reply.proof.payload_hex))

    signature_message = bytearray()
    signature_message.extend(bytes.fromhex("ffff"))
    signature_message.extend("ton-connect".encode())
    signature_message.extend(hashlib.sha256(message).digest())

    try:
        # verify ton_account.public_key
        verify_key = VerifyKey(bytes.fromhex(ton_account.public_key), HexEncoder)
        verify_key.verify(hashlib.sha256(signature_message).digest(), bytes.fromhex(reply.proof.signature))
        # decode payload
        decoded: TonProofPayload = decode_payload(reply.proof.payload_hex)
        return True, decoded, Address(ton_account.raw_address)

    except Exception as e:
        print(e)

    return False, None, None
