from app.dao.manager import DatabaseManager
from app.dao.impl.mongo_manager import MongoManager


async def get_db() -> DatabaseManager:
    return MongoManager()
