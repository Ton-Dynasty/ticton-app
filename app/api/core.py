from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.jobs.core import wait_for_ring_success, wait_for_tick_success
from app.models.core import Alarm, CreatePositionRequest
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models.telegram import TelegramUser
from app.api.middleware.auth import verify_tg_token
from ticton import TicTonAsyncClient

CoreRouter = APIRouter(prefix="/core", tags=["core"])


@CoreRouter.get("/alarms", response_model=List[Alarm])
async def get_my_active_alarms(telegram_id: int, manager: DatabaseManager = Depends(get_db)):
    try:
        # find alarms with telegram_id, and status is not closed
        result = manager.db["alarms"].find({"telegram_id": telegram_id, "status": {"$ne": "closed"}}).sort("created_at", -1)
        result = [Alarm(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms/closed")
async def get_my_closed_alarms(telegram_id: int, manager: DatabaseManager = Depends(get_db)):
    try:
        # find alarms with telegram_id, and status is closed
        result = manager.db["alarms"].find({"telegram_id": telegram_id, "status": "closed"}).sort("created_at", -1)
        result = [Alarm(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.get("/alarms")
async def get_alarms_by_pair_id(pair_id: str, manager: DatabaseManager = Depends(get_db)):
    try:
        # find alarms with pair_id
        result = manager.db["alarms"].find({"pair_id": pair_id, "status": {"$ne": "closed"}}).sort("created_at", -1)
        result = [Alarm(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.post("", description="User calls tick method in frontend and send oracle address and alarm_id to backend.")
async def tick_alarm(
    req: CreatePositionRequest,
    bg_tasks: BackgroundTasks,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
):

    try:
        # TODO: Tick here
        pair = manager.db["pairs"].find_one({"id": req.pair_id})
        oracle_address = pair.get("oracle_address")
        pos = Alarm(**req.model_dump(), telegram_id=tg_user.id, status="wait_tick")
        result = manager.db["alarms"].insert_one(pos.model_dump())
        bg_tasks.add_task(wait_for_tick_success, alarm_id=req.alarm_id, db=manager)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Success"})

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.put("", description="User calls ring method in frontend, and send alarm_id and oracle address to backend")
async def ring_alarm(
    position_id: str,
    bg_tasks: BackgroundTasks,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
):
    try:
        # check if position exists
        result = manager.db["alarms"].find_one({"id": position_id, "telegram_id": tg_user.id})
        if result is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Position not found"},
            )
        # check if position is active
        pos = Alarm(**result)
        if pos.status == False:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Position already closed"},
            )

        pair = manager.db["pairs"].find_one({"id": pos.pair_id})
        oracle_address = pair.get("oracle_address")
        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)
        result = manager.db["alarms"].update_one(
            {"id": position_id, "telegram_id": tg_user.id},
            {"$set": {"status": "wait_ring"}},
        )
        if result.modified_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Position not found"},
            )
        bg_tasks.add_task(wait_for_ring_success, alarm_id=pos.alarm_id, db=manager, cache=client.cache_manager)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
