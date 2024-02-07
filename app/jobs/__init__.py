from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler
import asyncio
from typing import Callable


def get_scheduler() -> BaseScheduler:
    return AsyncIOScheduler()
