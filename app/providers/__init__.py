from ticton import TicTonAsyncClient
from app.providers.impl.redis_manger import RedisManager
from app.providers.manager import DatabaseManager, CacheManager
from app.providers.impl.mongo_manager import MongoManager
from pytoncenter import get_client, AsyncTonCenterClientV3


async def get_db() -> DatabaseManager:
    return MongoManager()


async def get_cache() -> CacheManager:
    return RedisManager()


async def get_toncenter() -> AsyncTonCenterClientV3:
    return get_client(version="v3", network="testnet")
