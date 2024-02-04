from datetime import datetime
import json
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db, get_cache
from app.dao.manager import CacheManager
from app.models.core import CreatePairRequest, Pair
from app.models.provider import Provider, CreateProviderRequest, PriceResponse, UpdatePriceRequest
from app.settings import Settings, get_settings
from fastapi.encoders import jsonable_encoder
from ticton import TicTonAsyncClient


ProviderRouter = APIRouter(prefix="/provider", tags=["provider"])


@ProviderRouter.get("/pairs", response_model=List[Pair], description="Get available pairs")
async def get_pairs(db: DatabaseManager = Depends(get_db)):
    # TODO: get pairs from mongodb
    try:
        result = db.db["pairs"].find()
        result = [Pair(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@ProviderRouter.post("/pairs", description="Add new pair")
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


@ProviderRouter.get("", response_model=List[Provider], description="Get providers by pair id")
async def get_providers_by_pair_id(pair_id: str, manager: DatabaseManager = Depends(get_db)):
    try:
        result = manager.db["providers"].find({"pairs": {"$elemMatch": {"id": pair_id}}})
        result = [Provider(**i) for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(result))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@ProviderRouter.post("", description="Create a new provider", response_model=Provider)
async def create_provider(request: CreateProviderRequest, manager: DatabaseManager = Depends(get_db)):
    # TODO: only ton dynasty can create provider
    try:
        # Check if provider already exists
        existing_provider = manager.db["providers"].find_one({"name": request.name})
        if existing_provider and existing_provider.get("name"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Provider already exists"},
            )

        # Create new provider
        new_provider = Provider(**request.model_dump())
        result = manager.db["providers"].insert_one(new_provider.model_dump())
        print(result)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Success"})
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@ProviderRouter.get("/price", response_model=PriceResponse, description="Get price of a pair")
async def get_price(
    provider_id: str,
    pair_id: str,
    manager: DatabaseManager,
    cache: CacheManager = Depends(get_cache),
):
    provider = manager.db["providers"].find_one({"id": provider_id})
    if provider is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Provider not found"},
        )
    provider = Provider(**provider)
    resp = await cache.client.get(f"price:{provider_id}:{pair_id}")
    if resp is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Price not found"},
        )
    return PriceResponse(**json.loads(resp))


@ProviderRouter.put("/price", description="Update price of a pair in a provider")
async def update_price(
    provider_id: str,
    infos: List[UpdatePriceRequest],
    manager: DatabaseManager = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
    settings: Settings = Depends(get_settings),
):
    if settings.TICTON_MODE != "dev":
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": "Forbidden"})

    # check if every pair in info.pairs is in collection
    result = manager.db["pairs"].find({"id": {"$in": [x.pair_id for x in infos]}})
    if result.modified_count == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Pair not found"},
        )

    # get provider from mongodb
    provider = Provider(**manager.db["providers"].find_one({"id": provider_id}))
    if provider is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Provider not found"},
        )

    # update price in redis
    for info in infos:
        # find info.pair_id in collections
        p = manager.db["pairs"].find_one({"id": info.pair_id})
        if p is None:
            continue
        pair = Pair(**p)
        cache.client.set(f"price:{provider_id}:{pair.id}", PriceResponse(price=info.price, timestamp=datetime.now()).model_dump_json())
        cache.client.set(f"price:debug:{provider.name}:{pair.base_asset_symbol}/{pair.quote_asset_symbol}", info.price)
