from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.models.core import Position, CreatePositionRequest
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models.telegram import TelegramUser
from app.api.middleware.auth import verify_tg_token

CoreRouter = APIRouter(prefix="/core", tags=["core"])


@CoreRouter.get("", response_model=List[Position])
async def get_postions_by_id(
    telegram_id: int, manager: DatabaseManager = Depends(get_db)
):
    try:
        result = manager.db["positions"].find({"telegram_id": telegram_id})
        result = [Position(**i) for i in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=jsonable_encoder(result)
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@CoreRouter.post("")
async def create_position(
    req: CreatePositionRequest,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
):
    # TODO: Tick here
    try:
        pos = Position(**req.model_dump(), telegram_id=tg_user.id)
        result = manager.db["positions"].insert_one(pos.model_dump())
        print(result)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content={"message": "Success"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
