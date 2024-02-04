from pydoc import describe
from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.models.core import CreatePairRequest, Pair
from app.models.provider import Provider, CreateProviderRequest, PriceResponse
from fastapi.encoders import jsonable_encoder


ProviderRouter = APIRouter(prefix="/provider", tags=["provider"])


@ProviderRouter.get(
    "/pairs", response_model=List[Pair], description="Get available pairs"
)
async def get_pairs(db: DatabaseManager = Depends(get_db)):
    # TODO: get pairs from mongodb
    pass


@ProviderRouter.post("/pairs", description="Add new pair")
async def create_pair(
    request: CreatePairRequest, db: DatabaseManager = Depends(get_db)
):
    # TODO: only ton dynasty can create pair
    # TODO: call tic ton sdk to create pair
    pass


@ProviderRouter.get(
    "", response_model=List[Provider], description="Get providers by pair id"
)
async def get_providers_by_pair_id(
    pair_id: str, manager: DatabaseManager = Depends(get_db)
):
    try:
        result = manager.db["providers"].find(
            {"pairs": {"$elemMatch": {"id": pair_id}}}
        )
        result = [Provider(**i) for i in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK, content=jsonable_encoder(result)
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@ProviderRouter.post("", description="Create a new provider", response_model=Provider)
async def create_provider(
    request: CreateProviderRequest, manager: DatabaseManager = Depends(get_db)
):
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
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, content={"message": "Success"}
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)},
        )


@ProviderRouter.get(
    "/price", response_model=PriceResponse, description="Get price of a pair"
)
async def get_price(
    provider_id: str, pair_id: str, db: DatabaseManager = Depends(get_db)
):
    # TODO: get price from redis
    pass
