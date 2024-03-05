import asyncio
import json
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.providers import get_db
from app.providers import get_cache
from app.providers.manager import CacheManager, DatabaseManager
from app.jobs.core import subscribe_oracle
from app.jobs.price import get_exchanges, set_price
from app.models.core import Asset, PriceFeed, CreatePairRequest
from app.jobs import get_scheduler
from app.models.core import Pair
from ticton import TicTonAsyncClient
from apscheduler.schedulers.base import BaseScheduler

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
        client: TicTonAsyncClient = await TicTonAsyncClient.init(oracle_addr=request.oracle_address)

        pair = Pair(
            oracle_address=request.oracle_address,
            base_asset_address=client.metadata.base_asset_address,
            quote_asset_address=client.metadata.quote_asset_address,
            base_asset_symbol="TON",
            quote_asset_symbol="USDT",
            base_asset_decimals=client.metadata.base_asset_decimals,
            quote_asset_decimals=client.metadata.quote_asset_decimals,
        )
        result = db.db["pairs"].insert_one(pair.model_dump())
        task = asyncio.create_task(subscribe_oracle(client), name=f"subscribe_oracle_{request.oracle_address}")
        print("Background Task Created", task)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.get("/price", response_model=List[PriceFeed], description="Get price feeds of a specific pair")
async def get_price_feeds(pair_id: str, cache: CacheManager = Depends(get_cache), db: DatabaseManager = Depends(get_db)):
    try:
        # find pair by pair id
        pair = db.db["pairs"].find_one({"id": pair_id})
        pair = Pair(**pair)
        symbol = f"{pair.base_asset_symbol.upper()}/{pair.quote_asset_symbol.upper()}"
        iter = cache.client.scan_iter(f"price:*:{symbol}")
        result = [PriceFeed(**json.loads(cache.client.get(i))) for i in iter]  # type: ignore
        print(result)
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.delete("/debug/pairs", description="Delete pair")
async def debug_delete_pair(
    db: DatabaseManager = Depends(get_db),
):
    try:
        result = db.db["pairs"].delete_many({})
        print(result)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.post("/debug/pairs", description="Add new pair")
async def debug_create_pair(
    base_asset_symbol: str,
    quote_asset_symbol: str,
    base_asset_image_url: str,
    quote_asset_image_url: str,
    db: DatabaseManager = Depends(get_db),
):
    try:
        pair = Pair(
            oracle_address="debug",
            base_asset_address="debug-base-asset-address",
            quote_asset_address="debug-quote-asset-address",
            base_asset_symbol=base_asset_symbol,
            quote_asset_symbol=quote_asset_symbol,
            base_asset_decimals=9,
            quote_asset_decimals=6,
            base_asset_image_url=base_asset_image_url,
            quote_asset_image_url=quote_asset_image_url,
        )
        result = db.db["pairs"].insert_one(pair.model_dump())
        print(result)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
