from abc import ABC
from app.dao.manager import CacheManager, DatabaseManager
from app.models.provider import PriceResponse, Provider
import ccxt.async_support as ccxt
from ccxt import Exchange
