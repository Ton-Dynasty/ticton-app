from fastapi import Depends
from ticton import TicTonAsyncClient
from pytoncenter import get_client, AsyncTonCenterClientV3

from app.settings import Settings, get_settings


async def get_ton_center_client(settings: Settings = Depends(get_settings)) -> AsyncTonCenterClientV3:
    return get_client(version="v3", network="testnet", api_key=settings.TICTON_TONCENTER_API_KEY)


async def get_ticton_client(oracle_address: str, settings: Settings = Depends(get_settings)) -> TicTonAsyncClient:
    return await TicTonAsyncClient.init(
        mnemonics="unset",
        oracle_addr=oracle_address,
        testnet=settings.TICTON_NETWORK == "testnet",
        toncenter_api_key=settings.TICTON_TONCENTER_API_KEY,
    )
