from pydoc import describe
from typing import List
from fastapi import APIRouter, Depends, WebSocket, status
from fastapi.responses import JSONResponse
from app.dao import DatabaseManager, get_db
from app.models.strategy import Price, Strategy


StrategyRouter = APIRouter(prefix="/strategy", tags=["strategy"])


@StrategyRouter.get("", response_model=List[Strategy], description="List all strategies")
async def list_strategy(manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError


@StrategyRouter.get("/{strategy_name}/price", response_model=Price, description="Get price that provided by strategy")
async def get_price(strategy_name: str, manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError
