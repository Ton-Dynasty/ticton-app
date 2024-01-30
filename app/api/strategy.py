from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db


StrategyRouter = APIRouter(prefix="/strategy", tags=["strategy"])


@StrategyRouter.get("")
async def get_strategy(manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError
