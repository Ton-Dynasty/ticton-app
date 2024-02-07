import asyncio
from datetime import datetime, timedelta
import json
from operator import is_
from typing import List, Optional, Tuple

from fastapi import Depends
from app.dao import get_cache, get_db
from app.dao.manager import CacheManager, DatabaseManager
from app.models.core import PriceFeed, Pair
from ccxt import Exchange
import ccxt.async_support as ccxt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def get_exchanges() -> List[Exchange]:
    options = ["bybit", "gateio", "okx"]
    return [getattr(ccxt, opt)() for opt in options]


async def fetch_price(exchange: Exchange, symbol: str) -> Tuple[Optional[str], str, Optional[float]]:
    ticker = await exchange.fetch_ticker(symbol)
    return exchange.name, symbol, ticker.get("last", None)


async def set_price(exchanges: List[Exchange], cache: CacheManager, db: DatabaseManager):
    assert len(exchanges) > 0, "exchange list cannot be empty"
    # Find support pairs in database
    result = db.db["pairs"].find()
    pairs = [Pair(**i) for i in result]
    if len(pairs) == 0:
        logger.info("No pairs found in database")
        return
    symbols = [f"{p.base_asset_symbol.upper()}/{p.quote_asset_symbol.upper()}" for p in pairs]
    # for each exchange and symbol, get the price
    jobs = []
    for exchange in exchanges:
        for symbol in symbols:
            jobs.append(fetch_price(exchange, symbol))
    results: List[Tuple[Optional[str], str, float]] = await asyncio.gather(*jobs)
    for source, symbol, price in results:
        if price is None:
            continue
        feed = PriceFeed(source=source or "", price=price, last_updated_at=datetime.now())
        resp = cache.client.set(name=f"price:{source}:{symbol}", value=feed.model_dump_json())
        if not resp:
            logger.error(f"Failed to set price for {source}:{symbol}")
