from fastapi import APIRouter, Depends
from app.dao import DatabaseManager, get_db


StrategyRouter = APIRouter(prefix="/strategy", tags=["user"])


@StrategyRouter.get("/")
async def get_strategy(db: DatabaseManager = Depends(get_db)):
    return {"message": "Hello World"}
