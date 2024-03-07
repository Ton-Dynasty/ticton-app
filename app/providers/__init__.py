from ticton import TicTonAsyncClient
from app.providers.impl.redis_manger import RedisManager
from app.providers.impl.scheduler_manager import AsyncScheduler
from app.providers.manager import DatabaseManager, CacheManager
from app.providers.impl.mongo_manager import MongoManager


async def get_db() -> DatabaseManager:
    return MongoManager()


async def get_cache() -> CacheManager:
    return RedisManager()


async def get_scheduler():
    return AsyncScheduler()
