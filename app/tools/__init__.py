from fastapi import Depends
from ticton import TonCenterClient, TicTonAsyncClient

from app.settings import Settings, get_settings


def get_ton_center_client(settings: Settings = Depends(get_settings)) -> TonCenterClient:
    return TonCenterClient(api_key=settings.TICTON_TONCENTER_API_KEY, testnet=settings.TICTON_NETWORK == "testnet")
