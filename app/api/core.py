from fastapi import APIRouter, Depends
from app.dao import DatabaseManager, get_db


CoreRouter = APIRouter(prefix="/core", tags=["core"])


@CoreRouter.get("/")
async def get_core(db: DatabaseManager = Depends(get_db)):
    return {"message": "Hello World"}
