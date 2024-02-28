import redis
from app.providers.manager import CacheManager


class RedisManager(CacheManager):
    client: redis.Redis = None  # type: ignore

    def __new__(cls):
        """
        Singleton pattern
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(RedisManager, cls).__new__(cls)
        return cls.instance

    async def connect(
        self,
        host: str,
        port: int,
        password: str,
        db: int,
    ):
        self.client = redis.StrictRedis(host=host, port=port, db=db, password=password)

    async def disconnect(self):
        self.client.close()
