import asyncio
from datetime import datetime
from tonsdk.utils import Address
from nacl.utils import random

from pytonconnect import TonConnect
from pytonconnect.parsers import WalletInfo
import json


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


def decode_payload(payload_hex: str) -> dict:
    payload_bytes = bytearray.fromhex(payload_hex)
    timestamp_bytes = payload_bytes[-8:]
    timestamp = int.from_bytes(timestamp_bytes, "big")

    payload_str = payload_bytes[:-8].decode("utf-8")
    payload_dict = json.loads(payload_str)
    telegram_id = payload_dict["telegram_id"]
    return {
        "telegram_id": telegram_id,
        "timestamp": timestamp,
    }


def verify_tonproof_payload(payload: str, wallet_info: WalletInfo):
    if not wallet_info.check_proof(payload):
        print("Check proof failed")
        return False

    print("=====================================")
    print("After decode ", decode_payload(payload_hex=payload))
    print("=====================================")

    ts = int(payload[16:32], 16)
    if datetime.now().timestamp() > ts:
        print("Request timeout error")
        return False
    return True


async def main():
    proof_payload = generate_tonproof_payload(1234567890, 600)

    connector = TonConnect(
        manifest_url="https://raw.githubusercontent.com/XaBbl4/pytonconnect/main/pytonconnect-manifest.json"
    )

    def status_changed(wallet_info):
        print("wallet_info:", wallet_info)
        if wallet_info is not None:
            print("check_proof:", verify_tonproof_payload(proof_payload, wallet_info))

        unsubscribe()

    def status_error(e):
        print("connect_error:", e)

    unsubscribe = connector.on_status_change(status_changed, status_error)

    from pprint import pprint

    wallets_list = connector.get_wallets()
    pprint(wallets_list)

    generated_url = await connector.connect(
        wallets_list[1], {"ton_proof": proof_payload}
    )
    print("generated_url:", generated_url)

    print("Waiting 2 minutes to connect...")
    for i in range(120):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                print(
                    "Connected with address:",
                    Address(connector.account.address).to_string(True, True, True),
                )
            break

    if connector.connected:
        print("Waiting 2 minutes to disconnect...")
        asyncio.create_task(connector.disconnect())
        for i in range(120):
            await asyncio.sleep(1)
            if not connector.connected:
                print("Disconnected")
                break

    print("App is closed")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
