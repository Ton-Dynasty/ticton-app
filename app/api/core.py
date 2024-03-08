from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from app.providers import DatabaseManager, get_cache, get_db, get_scheduler
from app.models.common import PageResponse, Pagination
from app.models.core import Alarm, AlarmResponse, Pair
from fastapi.encoders import jsonable_encoder
from typing import List
from ticton import TicTonAsyncClient
from pytoncenter.address import Address
from app.providers.manager import CacheManager
from app.utils import get_pagination, calculate_time_elapse

CoreRouter = APIRouter(prefix="/core", tags=["core"])


@CoreRouter.get("/alarms/{address}/active", response_model=PageResponse[AlarmResponse])
async def get_my_active_alarms(address: str, manager: DatabaseManager = Depends(get_db), cache: CacheManager = Depends(get_cache), p: Pagination = Depends(get_pagination)):
    try:
        # find alarms with telegram_id, and status is not closed
        my_address = Address(address).to_string(False)
        pipeline = [
            {"$match": {"watchmaker": {"$eq": my_address}, "status": {"$ne": "closed"}}},
            {"$sort": {"alarm_id": -1}},
            {"$facet": {"paginatedResults": [{"$skip": p.skip}, {"$limit": p.limit}], "totalCount": [{"$count": "count"}]}},
        ]

        result = manager.db["alarms"].aggregate(pipeline)
        alarms = []
        total = 0
        for batch in result:
            alarms = [Alarm(**i) for i in batch["paginatedResults"]]
            total = batch["totalCount"][0]["count"] if batch["totalCount"] else 0

        responses = []

        unique_pairs = set([alarm.pair_id for alarm in alarms])
        pairs = manager.db["pairs"].find({"id": {"$in": list(unique_pairs)}})
        pairs = [Pair(**i) for i in pairs]
        pair_map = {pair.id: pair for pair in pairs}

        for alarm in alarms:
            pair = pair_map[alarm.pair_id]
            responses.append(
                AlarmResponse(
                    base_asset_image_url=pair.base_asset_image_url,
                    quote_asset_image_url=pair.quote_asset_image_url,
                    created_since=calculate_time_elapse(alarm.created_at),
                    price=alarm.price,
                    base_asset_scale=alarm.base_asset_scale,
                    quote_asset_scale=alarm.quote_asset_scale,
                    reward=alarm.reward,
                    min_base_asset_threshold=alarm.min_base_asset_threshold,
                    arbitrage_ratio=float(alarm.origin_remain_scale - alarm.remain_scale) / alarm.origin_remain_scale,
                    watchmaker=alarm.watchmaker,
                    alarm_id=alarm.id,
                    alarm_address=alarm.address,
                    remain_scale=alarm.remain_scale,
                )
            )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[AlarmResponse](items=responses, total=total)))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms/{address}/closed", response_model=PageResponse[AlarmResponse])
async def get_my_closed_alarms(address: str, manager: DatabaseManager = Depends(get_db), p: Pagination = Depends(get_pagination)):
    try:
        my_address = Address(address).to_string(False)
        # find alarms with telegram_id, and status is closed
        pipeline = [
            {"$match": {"watchmaker": {"$eq": my_address}, "status": {"$eq": "closed"}}},
            {"$sort": {"alarm_id": -1}},
            {"$facet": {"paginatedResults": [{"$skip": p.skip}, {"$limit": p.limit}], "totalCount": [{"$count": "count"}]}},
        ]

        result = manager.db["alarms"].aggregate(pipeline)
        alarms = []
        total = 0
        for batch in result:
            alarms = [Alarm(**i) for i in batch["paginatedResults"]]
            total = batch["totalCount"][0]["count"] if batch["totalCount"] else 0

        responses = []

        unique_pairs = set([alarm.pair_id for alarm in alarms])
        pairs = manager.db["pairs"].find({"id": {"$in": list(unique_pairs)}})
        pairs = [Pair(**i) for i in pairs]
        pair_map = {pair.id: pair for pair in pairs}

        for alarm in alarms:
            pair = pair_map[alarm.pair_id]
            responses.append(
                AlarmResponse(
                    base_asset_image_url=pair.base_asset_image_url,
                    quote_asset_image_url=pair.quote_asset_image_url,
                    created_since=calculate_time_elapse(alarm.created_at),
                    closed_since=calculate_time_elapse(alarm.closed_at),  # type: ignore
                    price=alarm.price,
                    base_asset_scale=alarm.base_asset_scale,
                    quote_asset_scale=alarm.quote_asset_scale,
                    reward=alarm.reward,
                    min_base_asset_threshold=alarm.min_base_asset_threshold,
                    arbitrage_ratio=float(alarm.origin_remain_scale - alarm.remain_scale) / alarm.origin_remain_scale,
                    watchmaker=alarm.watchmaker,
                    alarm_id=alarm.id,
                    alarm_address=alarm.address,
                    remain_scale=alarm.remain_scale,
                )
            )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[AlarmResponse](items=responses, total=total)))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms/active", response_model=PageResponse[AlarmResponse], description="Get all active alarms with non-zero remain scale")
async def get_alarms_by_pair_id(pair_id: str, manager: DatabaseManager = Depends(get_db), p: Pagination = Depends(get_pagination)):
    try:
        # get pair by pair_id
        pair_raw = manager.db["pairs"].find_one({"id": {"$eq": pair_id}})
        if pair_raw is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Pair not found"},
            )
        pair = Pair(**pair_raw)
        # find alarms with pair_id
        pipeline = [
            {"$match": {"pair_id": {"$eq": pair_id}, "status": {"$ne": "closed"}, "remain_scale": {"$gt": 0}}},
            {"$sort": {"alarm_id": -1}},
            {"$facet": {"paginatedResults": [{"$skip": p.skip}, {"$limit": p.limit}], "totalCount": [{"$count": "count"}]}},
        ]

        result = manager.db["alarms"].aggregate(pipeline)
        alarms = []
        total = 0
        for batch in result:
            alarms = [Alarm(**i) for i in batch["paginatedResults"]]
            total = batch["totalCount"][0]["count"] if batch["totalCount"] else 0

        responses = []
        for alarm in alarms:
            responses.append(
                AlarmResponse(
                    base_asset_image_url=pair.base_asset_image_url,
                    quote_asset_image_url=pair.quote_asset_image_url,
                    created_since=calculate_time_elapse(alarm.created_at),
                    price=alarm.price,
                    base_asset_scale=alarm.base_asset_scale,
                    quote_asset_scale=alarm.quote_asset_scale,
                    reward=alarm.reward,
                    min_base_asset_threshold=alarm.min_base_asset_threshold,
                    arbitrage_ratio=float(alarm.origin_remain_scale - alarm.remain_scale) / alarm.origin_remain_scale,
                    watchmaker=alarm.watchmaker,
                    alarm_id=alarm.id,
                    alarm_address=alarm.address,
                    remain_scale=alarm.remain_scale,
                )
            )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[AlarmResponse](items=responses, total=total)))
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
