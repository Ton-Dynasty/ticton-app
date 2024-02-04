from app.dao.impl.redis_manger import RedisManager
from app.dao.manager import DatabaseManager, CacheManager
from app.dao.impl.mongo_manager import MongoManager


async def get_db() -> DatabaseManager:
    return MongoManager()


async def get_redis() -> CacheManager:
    return RedisManager()
