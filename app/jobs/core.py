import asyncio
from hmac import new
from operator import ne
from pydoc import cli
import time

from pytz import utc
import pytz
from app.providers import get_cache, get_db, get_scheduler
from app.providers.manager import CacheManager, DatabaseManager, ScheduleManager
from app.models.core import Alarm
from ticton import TicTonAsyncClient
from pytoncenter.address import Address
from datetime import datetime, timedelta
from ticton.callbacks import OnTickSuccessParams, OnRingSuccessParams, OnWindSuccessParams
from app.models.core import Pair
from app.settings import Settings
from apscheduler.schedulers.base import BaseScheduler


async def on_tick_success(client: TicTonAsyncClient, params: OnTickSuccessParams, pair_info: Pair, **kwargs):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    try:
        manager: DatabaseManager = kwargs["manager"]

        # Put Alarm data to DB
        alarm = Alarm(
            id=params.new_alarm_id,
            address=Address(params.tx.in_msg.destination).to_string(False),  # type: ignore
            lt=params.tx.lt,
            pair_id=pair_info.id,
            oracle=Address(pair_info.oracle_address).to_string(False),
            created_at=datetime.fromtimestamp(params.created_at),
            closed_at=None,
            watchmaker=Address(params.watchmaker).to_string(False),
            base_asset_amount=client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals,
            quote_asset_amount=params.base_asset_price * (client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals),
            min_base_asset_threshold=client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals,
            origin_remain_scale=1,
            remain_scale=1,
            base_asset_scale=1,
            quote_asset_scale=1,
            status="active",
            reward=0.0,
            price=params.base_asset_price,
        )
        result = manager.db["alarms"].update_one(
            {"id": params.new_alarm_id},
            {"$set": alarm.model_dump()},
            upsert=True,
        )
        if result.acknowledged:
            print(
                "Tick Success | {ts} | {symbol} | alarm #{alarm_id} | price: {price}".format(
                    ts=datetime.fromtimestamp(params.tx.now, tz=utc).astimezone(pytz.timezone("Asia/Taipei")).isoformat(),
                    symbol=f"{pair_info.base_asset_symbol}/{pair_info.quote_asset_symbol}",
                    alarm_id=params.new_alarm_id,
                    price=params.base_asset_price,
                )
            )
    except Exception as e:
        import traceback

        print(traceback.format_exc())


async def on_ring_success(client: TicTonAsyncClient, params: OnRingSuccessParams, pair_info: Pair, **kwargs):
    """
    Wait for ring success.
    UPDATES:
    - Update the alarm status to "closed".
    - Update the alarm reward.
    - Update leader board.
    """
    try:
        manager: DatabaseManager = kwargs["manager"]
        # check if alarm is exists
        alarm = manager.db["alarms"].find_one({"id": params.alarm_id})
        if alarm is None:
            raise Exception("on_ring_success: Alarm does not exist")
        else:
            # Update the alarm status to "closed" and update the reward.
            close_at = datetime.fromtimestamp(params.created_at)
            manager.db["alarms"].update_one(
                {"id": params.alarm_id},
                {"$set": {"status": "closed", "reward": params.reward, "closed_at": close_at}},
            )
        # Update leader board
        if params.receiver is not None and params.reward > 0:
            wallet_address = Address(params.receiver).to_string(False)
            manager.db["leaderboard"].update_one(
                {"address": wallet_address},
                {"$inc": {"reward": params.reward}},
                upsert=True,
            )

        print(
            "Ring Success | {ts} | {symbol} | alarm #{alarm_id} | reward: {reward}".format(
                ts=datetime.fromtimestamp(params.tx.now, tz=utc).astimezone(pytz.timezone("Asia/Taipei")).isoformat(),
                symbol=f"{pair_info.base_asset_symbol}/{pair_info.quote_asset_symbol}",
                alarm_id=params.alarm_id,
                reward=params.reward,
            )
        )
    except Exception as e:
        import traceback

        print(traceback.format_exc())


async def on_wind_success(client: TicTonAsyncClient, params: OnWindSuccessParams, pair_info: Pair, **kwargs):
    """
    Wait for wind success.
    UPDATES:
    - Check the new alarm id is exists.
    - Check the timekeeper is the watchmaker of the new alarm.
    - Update the remain scale of the alarm.
    """
    try:
        manager: DatabaseManager = kwargs["manager"]

        old_alarm_raw = manager.db["alarms"].find_one({"id": params.old_alarm_id})
        if old_alarm_raw is None:
            raise Exception("Old alarm does not exist")
        old_alarm = Alarm(**old_alarm_raw)

        # insert new alarm to database
        new_alarm = Alarm(
            id=params.new_alarm_id,
            address=Address(params.tx.in_msg.source).to_string(False),  # type: ignore
            lt=params.tx.lt,
            pair_id=pair_info.id,
            oracle=Address(pair_info.oracle_address).to_string(False),
            created_at=datetime.fromtimestamp(params.created_at, tz=utc),
            closed_at=None,
            price=params.new_price,
            base_asset_amount=old_alarm.base_asset_amount * 2,
            quote_asset_amount=old_alarm.quote_asset_amount * 2,
            min_base_asset_threshold=client.metadata.min_base_asset_threshold / 10**client.metadata.base_asset_decimals,
            origin_remain_scale=params.new_remain_scale,
            remain_scale=params.new_remain_scale,
            base_asset_scale=params.new_remain_scale,
            quote_asset_scale=params.new_remain_scale,
            status="active",
            reward=0.0,
            watchmaker=Address(params.timekeeper).to_string(False),
        )

        # upsert new alarm
        manager.db["alarms"].update_one(
            {"id": params.new_alarm_id},
            {"$set": new_alarm.model_dump()},
            upsert=True,
        )

        if params.old_remain_scale == 0:
            # update the old alarm status to "emptied" and remain scale
            manager.db["alarms"].update_one(
                {"id": params.old_alarm_id},
                {"$set": {"status": "emptied", "remain_scale": params.old_alarm_id}},
            )
        else:
            # update the old alarm remain scale
            manager.db["alarms"].update_one(
                {"id": params.old_alarm_id},
                {"$set": {"remain_scale": params.old_remain_scale}},
            )

        print(
            "Wind Success | {ts} | {symbol} | old alarm #{old_alarm_id} | old price {old_price} | new alarm #{new_alarm_id} | new price {new_price}".format(
                ts=datetime.fromtimestamp(params.tx.now, tz=utc).astimezone(pytz.timezone("Asia/Taipei")).isoformat(),
                symbol=f"{pair_info.base_asset_symbol}/{pair_info.quote_asset_symbol}",
                old_alarm_id=params.old_alarm_id,
                old_price=params.old_price,
                new_alarm_id=params.new_alarm_id,
                new_price=params.new_price,
            )
        )

    except Exception as e:
        import traceback

        print(traceback.format_exc())


async def subscribe_oracle(client: TicTonAsyncClient, **kwargs):
    """
    Subscribe to oracle address.
    """
    manager = await get_db()
    pair_info_raw = manager.db["pairs"].find_one({"oracle_address": client.oracle.to_string(False)})
    if pair_info_raw is None:
        raise Exception("subscribe_oracle: Pair does not exist")
    pair_info = Pair(**pair_info_raw)
    last_record = manager.db["alarms"].find({"oracle": pair_info.oracle_address}).sort({"created_at": -1}).limit(1)
    start_lt = "oldest"
    last_record = [Alarm(**i) for i in last_record]
    if len(last_record) == 1:
        start_lt = last_record[0].lt
    await client.subscribe(
        on_tick_success=on_tick_success,  # type: ignore
        on_ring_success=on_ring_success,  # type: ignore
        on_wind_success=on_wind_success,  # type: ignore
        start_lt=start_lt,
        manager=manager,
        pair_info=pair_info,
        **kwargs,
    )


async def init_subscriptions(db: DatabaseManager, scheduler: ScheduleManager):
    """
    Initialize the background jobs.
    """
    # get pairs from db
    pairs = db.db["pairs"].find()
    pairs = [Pair(**i) for i in pairs]

    # subscribe to oracle address
    for pair in pairs:
        if scheduler.scheduler.get_job(f"subscribe_oracle_{pair.oracle_address}") is None:
            client = await TicTonAsyncClient.init(oracle_addr=pair.oracle_address)
            scheduler.scheduler.add_job(
                subscribe_oracle,
                "date",
                next_run_time=datetime.now() + timedelta(seconds=5),
                kwargs={"client": client},
                id=f"subscribe_oracle_{pair.oracle_address}",
                name=f"subscribe_oracle_{pair.oracle_address}",
                replace_existing=True,
            )
