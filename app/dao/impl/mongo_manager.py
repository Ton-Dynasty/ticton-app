from app.dao.manager import DatabaseManager
from pymongo import MongoClient
from pymongo.database import Database
import os


class MongoManager(DatabaseManager):
    client: MongoClient = None  # type: ignore
    db: Database = None  # type: ignore

    def __new__(cls):
        """
        Singleton pattern
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(MongoManager, cls).__new__(cls)
        return cls.instance

    async def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        db_name: str,
    ):
        self.client = MongoClient(
            host=host,
            port=port,
            username=username,
            password=password,
            connect=True,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            timeoutMS=3000,
        )
        self.db = self.client.get_database(db_name)

    async def disconnect(self):
        self.client.close()
