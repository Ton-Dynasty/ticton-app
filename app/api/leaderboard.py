from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.dao import get_db
from app.dao.manager import DatabaseManager
from app.models import LeaderBoardRecord
from app.models.telegram import TelegramUser
from app.api.middleware.auth import verify_tg_token

LeaderBoardRouter = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@LeaderBoardRouter.get("", response_model=List[LeaderBoardRecord], description="Get users rank based on rewards, default rank is 10.")
async def get_leader_board(rank: int = 10, manager: DatabaseManager = Depends(get_db)):
    try:
        assert rank > 0, "Rank should be greater than 0."
        result = manager.db["leaderboard"].sort("rewards", -1).limit(rank)
        leaderboards = [LeaderBoardRecord(**record, rank=i + 1) for i, record in enumerate(result)]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(leaderboards))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})


@LeaderBoardRouter.get("/my", response_model=LeaderBoardRecord, description="Get current user rank based on rewards.")
async def get_my_leader_board(
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
):
    try:
        # get current user rank
        raise NotImplementedError
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
