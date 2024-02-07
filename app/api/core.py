from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
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
