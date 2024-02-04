from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.models.core import Position, CreatePositionRequest
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models.telegram import TelegramUser
from app.api.middleware.auth import verify_tg_token
from ticton import TicTonAsyncClient

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

    try:
        # TODO: Tick here
        pair = manager.db["pairs"].find_one({"id": req.pair_id})
        oracle_address = pair.get("oracle_address")
        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)
        price = req.quote_asset_amount / req.base_asset_amount
        await client.tick(price)
        pos = Position(**req.model_dump(), telegram_id=tg_user.id, status="wait_tick")

        print(tg_user.id)
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


@CoreRouter.put("")
async def close_position(
    position_id: str,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
):
    try:
        # check if position exists
        result = manager.db["positions"].find_one(
            {"id": position_id, "telegram_id": tg_user.id}
        )
        if result is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Position not found"},
            )
        # check if position is active
        pos = Position(**result)
        if pos.status == False:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Position already closed"},
            )

        print("1")
        # TODO: Ring the position
        pair = manager.db["pairs"].find_one({"id": pos.pair_id})
        oracle_address = pair.get("oracle_address")
        client = await TicTonAsyncClient.init(oracle_addr=oracle_address)
        print("2")
        ring_result = await client.ring(alarm_id=22)
        print(ring_result)
        print("3")
        result = manager.db["positions"].update_one(
            {"id": position_id, "telegram_id": tg_user.id},
            {"$set": {"status": "wait_ring"}},
        )
        print(result)
        # if result nModified == 0, means no document is updated
        if result.modified_count == 0:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Position not found"},
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": "Success"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
