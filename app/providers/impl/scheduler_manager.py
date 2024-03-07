from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.providers.manager import ScheduleManager


class AsyncScheduler(ScheduleManager):
    _scheduler: AsyncIOScheduler = None  # type: ignore
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._scheduler = AsyncIOScheduler()
        return cls._instance

    @property
    def scheduler(self) -> AsyncIOScheduler:
        return self._scheduler
