from app.dao.manager import DatabaseManager, RedisManager
from app.dao.impl.mongo_manager import MongoManager


async def get_db() -> DatabaseManager:
    return MongoManager()


async def get_redis() -> RedisManager:
    return RedisManager()
