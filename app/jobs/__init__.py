from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler


def get_scheduler() -> BaseScheduler:
    return AsyncIOScheduler()
