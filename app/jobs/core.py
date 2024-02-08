from pydoc import cli
from app.dao import get_cache, get_db
from app.dao.manager import CacheManager, DatabaseManager
from app.models.core import Alarm
from ticton import TicTonAsyncClient
from tonsdk.utils import Address
from datetime import datetime


async def on_tick_success(watchmaker: str, base_asset_price: float, new_alarm_id: int, created_at: int):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    try:
        price = round(float(base_asset_price), 9)
        watchmaker = Address(watchmaker).to_string(True)
        manager = await get_db()
        # Get User's Telegram Id from DB by watchmaker address
        telegram_id = manager.db["users"].find_one({"wallet": watchmaker}).get("telegram_id")

        pair_id = await manager.db["alarms"].find_one({"id": new_alarm_id})["pair_id"]

        oracle_address = await manager.db["pairs"].find_one({"id": pair_id})["oracle_address"]

        # Get Pair Id from DB by Oracle Address
        pair_id = manager.db["pairs"].find_one({"oracle_address": oracle_address}).get("pair_id")

        # Init TicTonAsyncClient
        client: TicTonAsyncClient = await TicTonAsyncClient.init(oracle_addr=oracle_address)

        # Get Alarm's watchmaker
        alarm = await client.check_alarms([new_alarm_id])
        alarm_state = alarm[new_alarm_id]["state"]

        # Check if alarm state is active
        if alarm_state != "active":
            raise Exception("Tick failed, alarm state is not active")
        else:
            print("Tick success, alarm state is active")

        # Get Alarm metadata
        alarm_address = alarm[new_alarm_id]["alarm_address"]
        alarm_metadata = await client.get_alarm_info(alarm_address)
        base_asset_amount = 1  # alarm_metadata.base_asset_amount
        quote_asset_amount = price  # alarm_metadata.quote_asset_amount
        alarm_watchmaker = alarm_metadata["watchmaker"]

        # Check if alarm watchmaker is matched
        if alarm_watchmaker != watchmaker:
            raise Exception("Tick failed, watchmaker is not matched")
        else:
            print("Tick success, watchmaker is matched")

        # Put Alarm data to DB
        alarm = Alarm(
            telegram_id=telegram_id,
            pair_id=pair_id,
            oracle=oracle_address,
            id=new_alarm_id,
            created_at=datetime.fromtimestamp(created_at),
            closed_at=None,
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

    except Exception as e:
        raise Exception(str(e))


async def on_ring_success(alarm_id: int, created_at: int, origin: str, receiver: str, amount: int):
    """
    Wait for ring success.
    UPDATES:
    - Update the alarm status to "closed".
    - Update the alarm reward.
    - Update leader board.
    """
    try:
        # check the alarm is uninitialized
        client: TicTonAsyncClient = await TicTonAsyncClient.init()
        alarm = await client.check_alarms([alarm_id])
        alarm_state = alarm[alarm_id]["state"]

        if alarm_state != "uninitialized":
            raise Exception("Ring failed, alarm state is not uninitialized")

        manager: DatabaseManager = await get_db()
        # Update the alarm status to "closed" and update the reward.
        reward = amount / 10**6  # Convert to human readable format
        close_at = datetime.fromtimestamp(created_at)
        await manager.db["alarms"].update_one(
            {"id": alarm_id},
            {"$set": {"status": "closed", "reward": reward, "closed_at": close_at}},
        )
        # Update leader board
        wallet_address = Address(receiver).to_string(True)
        # get the user_id by wallet address
        user = await manager.db["users"].find_one({"wallet_address": wallet_address}, {"telegram_id": 1})
        await manager.db["leaderboard"].update_one(
            {"user_id": user["telegram_id"]},
            {"$inc": {"rewards": reward}},
            upsert=True,
        )
    except Exception as e:
        raise Exception(str(e))


async def on_wind_success(
    timekeeper: str,
    alarm_id: int,
    new_base_asset_price: float,
    remain_scale: int,
    new_alarm_id: int,
    created_at: int,
):
    """
    Wait for wind success.
    UPDATES:
    - Check the new alarm id is exists.
    - Check the timekeeper is the watchmaker of the new alarm.
    - Update the remain scale of the alarm.
    """
    try:
        manager = await get_db()
        timekeeper = Address(timekeeper).to_string(True)
        price = round(new_base_asset_price, 9)
        telegram_id = await manager.db["users"].find_one({"wallet": timekeeper})["telegram_id"]
        if telegram_id is None:
            raise Exception("Timekeeper is not exists")

        pair_id = await manager.db["alarms"].find_one({"id": alarm_id})["pair_id"]

        oracle_address = await manager.db["pairs"].find_one({"id": pair_id})["oracle_address"]

        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)
        alarm = await client.check_alarms([new_alarm_id])
        if alarm[new_alarm_id]["state"] != "active":
            raise Exception("New alarm state is not active")

        new_alarm_address = alarm[new_alarm_id]["address"]

        # get new alarm metadata
        new_alarm = await client.get_alarm_info(new_alarm_address)

        if new_alarm["watchmaker_address"] != timekeeper:
            raise Exception("Timekeeper is not the watchmaker of the new alarm")

        # insert new alarm to database
        new_alarm_info = Alarm(
            telegram_id=telegram_id,
            id=new_alarm_id,
            pair_id=pair_id,
            oracle=oracle_address,
            created_at=datetime.fromtimestamp(created_at),
            closed_at=None,
            base_asset_amount=new_alarm["base_asset_amount"],
            quote_asset_amount=new_alarm["quote_asset_amount"],
            remain_scale=new_alarm["remain_scale"],
            base_asset_scale=new_alarm["base_asset_scale"],
            quote_asset_scale=new_alarm["quote_asset_scale"],
            status=alarm[new_alarm_id]["state"],
            reward=0.0,
        )

        insert_result = await manager.db["alarms"].insert_one(new_alarm_info.model_dump())

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

    except Exception as e:
        raise Exception(str(e))


async def subscribe_oracle(client: TicTonAsyncClient):
    """
    Subscribe to oracle address.
    """
    await client.subscribe(
        on_tick_success=on_tick_success,
        on_ring_success=on_ring_success,
        on_wind_success=on_wind_success,
    )
