import json
from typing import List
from urllib import response
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import Json
from app.models.common import PageResponse, Pagination
from app.providers import get_cache, get_db
from app.providers.manager import CacheManager, DatabaseManager
from app.models.leaderboard import LeaderboardRecord, LeaderboardRecordList, LeaderboardResponse, LeaderboardRecordResponse
from pytoncenter.address import Address

from app.utils import get_pagination

LeaderBoardRouter = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@LeaderBoardRouter.get("", response_model=LeaderboardResponse, description="Get current user rank based on rewards.")
async def get_leader_board(
    address: str,
    manager: DatabaseManager = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
):
    try:
        my_address = Address(address).to_string(False)

        # Calculate rank dynamically based on rewards, assuming 'reward' field is indexed for sorting
        cache_top_10 = cache.client.get("leaderboard_top_10")
        if cache_top_10 is not None:
            top_10_records = json.loads(cache_top_10)  # type: ignore
            top_10_records = LeaderboardRecordList(**top_10_records)
        else:
            top_10_records_raw = manager.db["leaderboard"].find().sort("reward", -1).limit(10)
            top_10_records = LeaderboardRecordList(leaderboard=[LeaderboardRecord(**r, rank=i + 1) for i, r in enumerate(top_10_records_raw)])
            cache.client.set("leaderboard_top_10", top_10_records.model_dump_json(), ex=60)

        if len(top_10_records.leaderboard) == 0:
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(LeaderboardResponse(current_address=my_address, current_rank=-1, current_reward=0.0, leaderboard=[])))

        # Get the rank of the current user
        user_rank = 0
        user_reward = 0.0
        current_user_record = manager.db["leaderboard"].find_one({"address": my_address})
        if current_user_record is not None:
            current_user_rank = manager.db["leaderboard"].count_documents({"reward": {"$gt": current_user_record["reward"]}}) + 1
            user_rank = current_user_rank
            user_reward = current_user_record["reward"]

        leaderboard_response = []
        for i, record in enumerate(top_10_records.leaderboard):
            is_current_user = record.address == my_address
            leaderboard_response.append(LeaderboardRecordResponse(address=record.address, rank=i + 1, reward=round(record.reward, 4), is_current_user=is_current_user))

        result = {"current_address": my_address, "current_reward": round(user_reward, 4), "current_rank": user_rank, "leaderboard": leaderboard_response}

        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(LeaderboardResponse(**result)))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})


@LeaderBoardRouter.get("/debug", response_model=PageResponse[LeaderboardRecord], description="Get leaderboard records with pagination")
async def get_leader_board_pagination(
    manager: DatabaseManager = Depends(get_db),
    p: Pagination = Depends(get_pagination),
):
    try:
        pipeline = [
            {"$sort": {"reward": -1}},
            {"$facet": {"paginatedResults": [{"$skip": p.skip}, {"$limit": p.limit}], "totalCount": [{"$count": "count"}]}},
        ]
        result = manager.db["leaderboard"].aggregate(pipeline)
        leaderboard_records = []
        total = 0
        for batch in result:
            leaderboard_records = [LeaderboardRecord(**b, rank=(i + 1) + p.skip) for i, b in enumerate(batch["paginatedResults"])]
            total = batch["totalCount"][0]["count"] if batch["totalCount"] else 0
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(PageResponse[LeaderboardRecord](items=leaderboard_records, total=total)))
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})
