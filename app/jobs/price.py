from app.dao.manager import CacheManager, DatabaseManager
from app.models.core import PriceFeed
import ccxt.async_support as ccxt
from ccxt import Exchange


def get_exchange(exchange: str) -> Exchange:
    return getattr(ccxt, exchange)()
