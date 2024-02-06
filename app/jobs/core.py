from app.dao import get_cache, get_db
from app.dao.manager import CacheManager, DatabaseManager
from app.models.core import Alarm
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ticton import TicTonAsyncClient
from tonsdk.utils import Address


def on_tick_success(alarm_id: int):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    pass


def on_ring_success(alarm_id: int):
    """
    Wait for ring success.
    UPDATES:
    - Update the position status to "closed".
    - Update the position reward.
    - Update leader board.
    """
    pass


async def on_wind_success(
    timekeeper: str,
    alarm_id: int,
    new_base_asset_price: float,
    remain_scale: int,
    new_alarm_id: int,
):
    """
    Wait for wind success.
    UPDATES:
    - Check the new alarm id is exists.
    - Check the timekeeper is the watchmaker of the new alarm.
    - Update the remain scale of the alarm.
    """
    try:
        manager = get_db()
        timekeeper = Address(timekeeper).to_string(False)
        price = round(new_base_asset_price, 9)
        telegram_id = await manager.db["users"].find_one({"wallet": timekeeper})[
            "telegram_id"
        ]
        if telegram_id is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Timekeeper is not registered"},
            )

        pair_id = await manager.db["alarms"].find_one({"id": alarm_id})["pair_id"]

        oracle_address = await manager.db["pairs"].find_one({"id": pair_id})[
            "oracle_address"
        ]

        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)
        alarm = await client.check_alarms([new_alarm_id])
        if alarm[new_alarm_id]["state"] != "active":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "New alarm is not active"},
            )

        new_alarm_address = alarm[new_alarm_id]["address"]

        # get new alarm metadata
        new_alarm = await client.get_alarm_info(new_alarm_address)

        if new_alarm["watchmaker_address"] != timekeeper:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": "Timekeeper is not the watchmaker of the new alarm"
                },
            )

        # insert new alarm to database
        new_alarm_info = Alarm(
            id=new_alarm_id,
            pair_id=pair_id,
            oracle=oracle_address,
            created_at=new_alarm["created_at"],
            base_asset_amount=new_alarm["base_asset_amount"],
            quote_asset_amount=new_alarm["quote_asset_amount"],
            remain_scale=new_alarm["remain_scale"],
            base_asset_scale=new_alarm["base_asset_scale"],
            quote_asset_scale=new_alarm["quote_asset_scale"],
            status=alarm[new_alarm_id]["state"],
            reward=0.0,
        )

        insert_result = await manager.db["alarms"].insert_one(
            new_alarm_info.model_dump()
        )

        if remain_scale == 0:
            # update the old alarm status to "emptied" and remain scale
            await manager.db["alarms"].update_one(
                {"id": alarm_id},
                {"$set": {"status": "emptied", "remain_scale": remain_scale}},
            )
        else:
            # update the old alarm remain scale
            await manager.db["alarms"].update_one(
                {"id": alarm_id},
                {"$set": {"remain_scale": remain_scale}},
            )

        insert_result = [Alarm(**i) for i in insert_result]
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=jsonable_encoder(insert_result)
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
