from app.dao import get_cache, get_db
from app.dao.manager import CacheManager, DatabaseManager
from ticton import TicTonAsyncClient
from tonsdk.utils import Address
from app.models.core import Alarm
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.encoders import jsonable_encoder

oracle_address = "kQDIuXyeKZ9-Bxezc2UaI6Ct8megUpIYwAjCIWOKPhkMMrip"


async def on_tick_success(
    watchmaker: str, base_asset_price: float, new_alarm_id: int, created_at: int
):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    try:
        price = round(float(base_asset_price), 9)
        watchmaker = Address(watchmaker).to_string(False)
        manager = get_db()
        # Get User's Telegram Id from DB by watchmaker address
        telegram_id = (
            manager.db["users"].find_one({"wallet": watchmaker}).get("telegram_id")
        )

        # Get Pair Id from DB by Oracle Address
        pair_id = (
            manager.db["pairs"]
            .find_one({"oracle_address": oracle_address})
            .get("pair_id")
        )

        # Init TicTonAsyncClient
        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)

        # Get Alarm's watchmaker
        alarm = await client.check_alarms([new_alarm_id])
        alarm_state = alarm[new_alarm_id]["state"]

        # Check if alarm state is active
        if alarm_state != "active":
            print("Tick failed, alarm state is not active")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Tick failed, Alarm state is not active"},
            )
        else:
            print("Tick success, alarm state is active")

        # Get Alarm metadata
        alarm_address = alarm[new_alarm_id]["alarm_address"]
        alarm_metadata = await client.get_alarm_info(alarm_address)
        base_asset_amount = 1  # alarm_metadata.base_asset_amount
        quote_asset_amount = price  # alarm_metadata.quote_asset_amount
        alarm_watchmaker = alarm_metadata.watchmaker

        # Check if alarm watchmaker is matched
        if alarm_watchmaker != watchmaker:
            print("Tick failed, watchmaker is not matched")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Tick failed, Watchmaker is not matched"},
            )
        else:
            print("Tick success, watchmaker is matched")

        # Put Alarm data to DB
        alarm = Alarm(
            telegram_id=telegram_id,
            pair_id=pair_id,
            oracle=oracle_address,
            id=new_alarm_id,
            created_at=created_at,
            base_asset_amount=base_asset_amount,
            quote_asset_amount=quote_asset_amount,
            remain_scale=1,
            base_asset_scale=1,
            quote_asset_scale=1,
            status="active",
            reward=0.0,
        )
        result = manager.db["alarms"].insert_one(alarm.model_dump())
        result = [Alarm(**i) for i in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=jsonable_encoder(result)
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


def on_ring_success(alarm_id: int):
    """
    Wait for ring success.
    UPDATES:
    - Update the position status to "closed".
    - Update the position reward.
    - Update leader board.
    """
    pass


def on_wind_success():
    pass
