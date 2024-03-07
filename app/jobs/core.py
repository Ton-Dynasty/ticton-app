import asyncio
from pydoc import cli
from app.providers import get_cache, get_db
from app.providers.manager import CacheManager, DatabaseManager
from app.models.core import Alarm
from ticton import TicTonAsyncClient
from tonsdk.utils import Address
from datetime import datetime
from ticton.callbacks import OnTickSuccessParams, OnRingSuccessParams, OnWindSuccessParams
from app.models.core import Pair
from app.settings import Settings
from app.tools import get_ticton_client


async def on_tick_success(client: TicTonAsyncClient, params: OnTickSuccessParams, **kwargs):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    try:
        price = round(float(params.base_asset_price), 9)
        watchmaker = Address(params.watchmaker).to_string(True)
        manager = await get_db()

        pair_id = await manager.db["alarms"].find_one({"id": params.new_alarm_id})["pair_id"]

        oracle_address = await manager.db["pairs"].find_one({"id": pair_id})["oracle_address"]

        # Get Pair Id from DB by Oracle Address
        pair_id = manager.db["pairs"].find_one({"oracle_address": oracle_address}).get("pair_id")

        # Get Alarm's watchmaker
        alarm = await client.check_alarms([params.new_alarm_id])
        alarm_state = alarm[params.new_alarm_id]["state"]

        # Check if alarm state is active
        if alarm_state != "active":
            raise Exception("Tick failed, alarm state is not active")
        else:
            print("Tick success, alarm state is active")

        # Get Alarm metadata
        alarm_address = alarm[params.new_alarm_id]["alarm_address"]
        alarm_metadata = await client.get_alarm_metadata(alarm_address)
        base_asset_amount = 1  # alarm_metadata.base_asset_amount
        quote_asset_amount = price  # alarm_metadata.quote_asset_amount
        alarm_watchmaker = alarm_metadata.watchmaker_address

        # Check if alarm watchmaker is matched
        if alarm_watchmaker != watchmaker:
            raise Exception("Tick failed, watchmaker is not matched")
        else:
            print("Tick success, watchmaker is matched")

        # Put Alarm data to DB
        alarm = Alarm(
            id=params.new_alarm_id,
            pair_id=pair_id,
            oracle=oracle_address,
            created_at=datetime.fromtimestamp(params.created_at),
            closed_at=None,
            base_asset_amount=base_asset_amount,
            quote_asset_amount=quote_asset_amount,
            min_base_asset_threshold=client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals,
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


async def on_ring_success(client: TicTonAsyncClient, params: OnRingSuccessParams, **kwargs):
    """
    Wait for ring success.
    UPDATES:
    - Update the alarm status to "closed".
    - Update the alarm reward.
    - Update leader board.
    """
    try:
        # check the alarm is uninitialized
        alarm = await client.check_alarms([params.alarm_id])
        alarm_state = alarm[params.alarm_id]["state"]

        if alarm_state != "uninitialized":
            raise Exception("Ring failed, alarm state is not uninitialized")

        manager: DatabaseManager = await get_db()
        # Update the alarm status to "closed" and update the reward.
        close_at = datetime.fromtimestamp(params.created_at)
        await manager.db["alarms"].update_one(
            {"id": params.alarm_id},
            {"$set": {"status": "closed", "reward": params.reward, "closed_at": close_at}},
        )
        # Update leader board
        wallet_address = Address(params.receiver).to_string(True)
        await manager.db["leaderboard"].update_one(
            {"address": wallet_address},
            {"$inc": {"rewards": params.reward}},
            upsert=True,
        )
    except Exception as e:
        raise Exception(str(e))


async def on_wind_success(client: TicTonAsyncClient, params: OnWindSuccessParams, **kwargs):
    """
    Wait for wind success.
    UPDATES:
    - Check the new alarm id is exists.
    - Check the timekeeper is the watchmaker of the new alarm.
    - Update the remain scale of the alarm.
    """
    try:
        manager = await get_db()
        timekeeper = Address(params.timekeeper).to_string(True)
        price = round(params.new_base_asset_price, 9)

        pair_id = await manager.db["alarms"].find_one({"id": params.alarm_id})["pair_id"]

        oracle_address = await manager.db["pairs"].find_one({"id": pair_id})["oracle_address"]

        alarm = await client.check_alarms([params.new_alarm_id])
        if alarm[params.new_alarm_id]["state"] != "active":
            raise Exception("New alarm state is not active")

        new_alarm_address = alarm[params.new_alarm_id]["address"]

        # get new alarm metadata

        new_alarm = await client.get_alarm_metadata(new_alarm_address)

        if new_alarm.watchmaker_address != timekeeper:
            raise Exception("Timekeeper is not the watchmaker of the new alarm")

        # insert new alarm to database
        new_alarm_info = Alarm(
            id=params.new_alarm_id,
            pair_id=pair_id,
            oracle=oracle_address,
            created_at=datetime.fromtimestamp(params.created_at),
            closed_at=None,
            base_asset_amount=new_alarm.base_asset_amount,
            quote_asset_amount=new_alarm.quote_asset_amount,
            min_base_asset_threshold=client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals,
            remain_scale=new_alarm.remain_scale,
            base_asset_scale=new_alarm.base_asset_scale,
            quote_asset_scale=new_alarm.quote_asset_scale,
            status=alarm[params.new_alarm_id]["state"],
            reward=0.0,
        )

        insert_result = await manager.db["alarms"].insert_one(new_alarm_info.model_dump())

        if params.remain_scale == 0:
            # update the old alarm status to "emptied" and remain scale
            await manager.db["alarms"].update_one(
                {"id": params.alarm_id},
                {"$set": {"status": "emptied", "remain_scale": params.remain_scale}},
            )
        else:
            # update the old alarm remain scale
            await manager.db["alarms"].update_one(
                {"id": params.alarm_id},
                {"$set": {"remain_scale": params.remain_scale}},
            )

        insert_result = [Alarm(**i) for i in insert_result]

    except Exception as e:
        raise Exception(str(e))


async def subscribe_oracle(client: TicTonAsyncClient):
    """
    Subscribe to oracle address.
    """
    await client.subscribe(
        on_tick_success=on_tick_success,  # type: ignore
        on_ring_success=on_ring_success,  # type: ignore
        on_wind_success=on_wind_success,  # type: ignore
        start_lt="oldest",
    )


async def initialize_jobs(settings: Settings, db: DatabaseManager):
    """
    Initialize the background jobs.
    """
    # get pairs from db
    pairs = await db.db["pairs"].find()
    pairs = [Pair(**i) for i in pairs]

    # subscribe to oracle address
    for pair in pairs:
        client = await TicTonAsyncClient.init(oracle_addr=pair.oracle_address)
        _ = asyncio.create_task(
            client.subscribe(
                on_tick_success=on_tick_success,  # type: ignore
                on_ring_success=on_ring_success,  # type: ignore
                on_wind_success=on_wind_success,  # type: ignore
                start_lt="oldest",
                db=db,
            )
        )
