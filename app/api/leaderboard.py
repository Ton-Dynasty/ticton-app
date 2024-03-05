from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.providers import get_db
from app.providers.manager import DatabaseManager
from app.models.leaderboard import LeaderBoardRecord
from pytoncenter.address import Address

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
    address: str,
    manager: DatabaseManager = Depends(get_db),
):
    try:
        raw_address = Address(address).to_string(False)
        # get current user rank
        result = manager.db["leaderboard"].find_one({"address": raw_address})
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(LeaderBoardRecord(**result)))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
