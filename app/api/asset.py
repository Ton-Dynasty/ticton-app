import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.dao import get_db
from app.dao import get_cache
from app.dao.manager import CacheManager, DatabaseManager
from app.models.core import Asset, PriceFeed, CreatePairRequest
from app.models.telegram import TelegramUser
from app.jobs import get_scheduler
from app.models.core import Pair
from app.api.middleware.auth import verify_tg_token
from ticton import TicTonAsyncClient


AssetRouter = APIRouter(prefix="/asset", tags=["asset"])


@AssetRouter.get("/pairs", response_model=List[Pair], description="Get available pairs")
async def get_pairs(db: DatabaseManager = Depends(get_db)):
    try:
        result = db.db["pairs"].find()
        result = [Pair(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.post("/pairs", description="Add new pair")
async def create_pair(request: CreatePairRequest, db: DatabaseManager = Depends(get_db)):
    # TODO: only ton dynasty can create pair
    try:
        # TODO: call tic ton sdk to create pair
        client = await TicTonAsyncClient.init(oracle_addr=request.oracle_address)

        pair = Pair(
            oracle_address=request.oracle_address,
            base_asset_address=client.metadata["base_asset_address"].to_string(),
            quote_asset_address=client.metadata["quote_asset_address"].to_string(),
            base_asset_symbol=client.metadata["base_asset_symbol"],
            quote_asset_symbol=client.metadata["quote_asset_symbol"],
            base_asset_decimals=client.metadata["base_asset_decimals"],
            quote_asset_decimals=client.metadata["quote_asset_decimals"],
        )
        result = db.db["pairs"].insert_one(pair.model_dump())
        print(result)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.get("", response_model=List[PriceFeed], description="Get price feeds of a specific pair")
async def get_price_feeds(pair_id: str, cache: CacheManager = Depends(get_cache)):
    try:
        # Find price feeds with key pattern "price_feed:*:{pair_id}"
        iter = cache.client.scan_iter(f"price_feed:*:{pair_id}")
        result = [json.loads(cache.client.get(i)) for i in iter]  # type: ignore
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
