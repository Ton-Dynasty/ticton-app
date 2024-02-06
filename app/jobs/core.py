from app.dao.manager import CacheManager, DatabaseManager


def wait_for_tick_success(alarm_id: int, db: DatabaseManager):
    """
    Wait for tick success and check the alarm id is exists.
    If the alarm id is exists, then:
    - Update the position status to "active".
    """
    pass


def wait_for_ring_success(alarm_id: int, db: DatabaseManager, cache: CacheManager):
    """
    Wait for ring success.
    UPDATES:
    - Update the position status to "closed".
    - Update the position reward.
    - Update leader board.
    """
    pass


def wait_for_wind_success():
    pass
