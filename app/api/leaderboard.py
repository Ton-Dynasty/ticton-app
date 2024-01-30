from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.dao import get_db
from app.dao.manager import DatabaseManager
from app.models import LeaderBoardRecord

LeaderBoardRouter = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@LeaderBoardRouter.get("", response_model=List[LeaderBoardRecord])
async def get_leader_board(page: int = 1, size: int = 20, manager: DatabaseManager = Depends(get_db)):
    try:
        assert page > 0 and size > 0
        skip = (page - 1) * size
        result = manager.db["leaderboard"].sort("rewards", -1).skip(skip).limit(size)
        leaderboards = [LeaderBoardRecord(**record) for record in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(leaderboards))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
