from app.dao import get_cache, get_db
from app.dao.manager import CacheManager, DatabaseManager
from ticton import TicTonAsyncClient


def on_tick_success(alarm_id: int):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    pass


def on_ring_success(alarm_id: int):
    """
    Wait for ring success.
    UPDATES:
    - Update the position status to "closed".
    - Update the position reward.
    - Update leader board.
    """
    pass


def on_wind_success():
    pass
