from pydoc import describe
from typing import List
from fastapi import APIRouter, Depends, WebSocket, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.models.core import CreatePairRequest, Pair
from app.models.provider import Provider, CreateProviderRequest, PriceResponse


ProviderRouter = APIRouter(prefix="/provider", tags=["provider"])


@ProviderRouter.get("/pairs", response_model=List[Pair], description="Get available pairs")
async def get_pairs(db: DatabaseManager = Depends(get_db)):
    # TODO: get pairs from mongodb
    pass


@ProviderRouter.post("/pairs", description="Add new pair")
async def create_pair(request: CreatePairRequest, db: DatabaseManager = Depends(get_db)):
    # TODO: only ton dynasty can create pair
    # TODO: call tic ton sdk to create pair
    pass


@ProviderRouter.get("", response_model=List[Provider], description="Get providers by pair id")
async def get_providers_by_pair_id(pair_id: str, db: DatabaseManager = Depends(get_db)):
    # TODO: get providers from mongodb
    pass


@ProviderRouter.post("", description="Create a new provider", response_model=Provider)
async def create_provider(request: CreateProviderRequest, db: DatabaseManager = Depends(get_db)):
    # TODO: only ton dynasty can create provider
    pass


@ProviderRouter.get("/price", response_model=PriceResponse, description="Get price of a pair")
async def get_price(provider_id: str, pair_id: str, db: DatabaseManager = Depends(get_db)):
    # TODO: get price from redis
    pass
