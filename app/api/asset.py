import asyncio
from datetime import datetime, timedelta
import json
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ticton import TicTonAsyncClient
from app.providers import get_db
from app.providers import get_cache
from app.providers import get_scheduler
from app.providers.manager import CacheManager, DatabaseManager, ScheduleManager
from app.jobs.core import subscribe_oracle
from app.jobs.price import get_exchanges, set_price
from app.models.core import Asset, PriceFeed, CreatePairRequest
from app.models.core import Pair
from ticton import TicTonAsyncClient
from apscheduler.schedulers.base import BaseScheduler
from app.settings import Settings, get_settings
from app.tools import get_ticton_client
from pytoncenter.address import Address
from pytoncenter import get_client
from pytoncenter.v3.models import GetSpecifiedJettonWalletRequest

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
async def create_pair(
    request: CreatePairRequest,
    db: DatabaseManager = Depends(get_db),
    settings: Settings = Depends(get_settings),
    scheduler: ScheduleManager = Depends(get_scheduler),
):
    # TODO: only ton dynasty can create pair
    try:
        client = await get_ticton_client(oracle_address=request.oracle_address, settings=settings)

        oracle_address = Address(request.oracle_address).to_string(False)

        pair = Pair(
            oracle_address=oracle_address,
            base_asset_address=Address(client.metadata.base_asset_address).to_string(False),
            quote_asset_address=Address(client.metadata.quote_asset_address).to_string(False),
            base_asset_symbol=client.metadata.base_asset_symbol,
            quote_asset_symbol=client.metadata.quote_asset_symbol,
            base_asset_decimals=client.metadata.base_asset_decimals,
            quote_asset_decimals=client.metadata.quote_asset_decimals,
            base_asset_image_url=request.base_asset_image_url,
            quote_asset_image_url=request.quote_asset_image_url,
        )
        result = db.db["pairs"].insert_one(pair.model_dump())
        if result.acknowledged:
            print("Pair Created", pair)
        scheduler.scheduler.add_job(
            subscribe_oracle,
            "date",
            next_run_time=datetime.now() + timedelta(seconds=5),
            kwargs={"client": client},
            id=f"subscribe_oracle_{pair.oracle_address}",
            name=f"subscribe_oracle_{pair.oracle_address}",
            replace_existing=True,
        )
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
        iter = cache.client.scan_iter(f"price$*${symbol}")
        result = [PriceFeed(**json.loads(cache.client.get(i))) for i in iter]  # type: ignore
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.get("/reward", description="Get the number of reward tokens in specified address currently")
async def get_reward_by_address(address: str, settings: Settings = Depends(get_settings)):
    try:
        my_address = Address(address).to_string(False)
        client = get_client(version="v3", network=settings.TICTON_NETWORK)
        request = GetSpecifiedJettonWalletRequest(owner_address=my_address, jetton_address="0:903d8c69172157c484a203f738db0358af3706736f4d7051eaaeea434e54f76b")
        result = await client.get_jetton_wallets(request)
        if result is None:
            return JSONResponse(status_code=status.HTTP_200_OK, content={"reward": 0})
        balance = result.balance / 10**9
        return JSONResponse(status_code=status.HTTP_200_OK, content={"reward": balance})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@AssetRouter.delete("/debug/pairs", description="Delete pair")
async def debug_delete_pair(
    pair_id: str,
    db: DatabaseManager = Depends(get_db),
    scheduler: BaseScheduler = Depends(get_scheduler),
):
    try:
        # get oracle address by pair id
        pair = db.db["pairs"].find_one({"id": pair_id})
        oracle_address = pair["oracle_address"]

        scheduler.remove_job(job_id=f"subscribe_oracle_{oracle_address}")

        # delete pair by pair id
        result = db.db["pairs"].delete_one({"id": pair_id})
        if result.acknowledged:
            print("Pair Deleted", pair_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )
