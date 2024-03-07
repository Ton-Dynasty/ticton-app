from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from app.providers import DatabaseManager, get_cache, get_db
from app.models.common import PageResponse, Pagination
from app.models.core import Alarm, AlarmResponse
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
        raw_address = Address(address).to_string(False)
        alarms = manager.db["alarms"].find({"watchmaker": {"$eq": raw_address}, "status": {"$ne": "closed"}}).limit(p.limit).skip(p.skip).sort("created_at", -1)
        alarms = [Alarm(**i) for i in alarms]
        total = manager.db["alarms"].count_documents({"watchmaker": {"$eq": raw_address}, "status": {"$ne": "closed"}})
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[Alarm](items=alarms, total=total)))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms/{address}/closed", response_model=PageResponse[AlarmResponse])
async def get_my_closed_alarms(address: str, manager: DatabaseManager = Depends(get_db), p: Pagination = Depends(get_pagination)):
    try:
        raw_address = Address(address).to_string(False)
        # find alarms with telegram_id, and status is closed
        alarms = manager.db["alarms"].find({"watchmaker": raw_address, "status": "closed"}).limit(p.limit).skip(p.skip).sort("closed_at", -1)
        alarms = [Alarm(**i) for i in alarms]
        total = manager.db["alarms"].count_documents({"watchmaker": raw_address, "status": "closed"})
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[Alarm](items=alarms, total=total)))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms", response_model=PageResponse[Alarm])
async def get_alarms_by_pair_id(pair_id: str, manager: DatabaseManager = Depends(get_db), p: Pagination = Depends(get_pagination)):
    try:
        # find alarms with pair_id
        alarms = manager.db["alarms"].find({"pair_id": pair_id, "status": {"$ne": "closed"}}).limit(p.limit).skip(p.skip).sort("created_at", -1)
        alarms = [Alarm(**i) for i in alarms]
        total = manager.db["alarms"].count_documents({"pair_id": pair_id, "status": {"$ne": "closed"}})
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[Alarm](items=alarms, total=total)))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
