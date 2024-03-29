import asyncio
from datetime import datetime, timedelta
from functools import cache
import json
from operator import is_
from typing import List, Optional, Tuple

from fastapi import Depends
from redis import Redis
import redis
from app.providers import get_cache, get_db
from app.providers.manager import CacheManager, DatabaseManager
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


async def fetch_price(exchange: Exchange, symbol: str, **kwargs) -> Tuple[Optional[str], str, Optional[float]]:
    try:
        ticker = await exchange.fetch_ticker(symbol)  # type: ignore
        return exchange.name, symbol, ticker.get("last", None)
    except Exception as e:
        logger.exception(f"Failed to fetch price for {exchange.name}:{symbol}. Reason: {e}")
        return None, symbol, None


async def set_price(exchanges: List[Exchange]):
    cache = await get_cache()
    db = await get_db()
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
        # TODO: Hard coded the price to 4 decimal places, should be configurable in the future
        feed = PriceFeed(source=source or "", price=round(price, 4), last_updated_at=datetime.now(), symbol=symbol)
        resp = cache.client.set(name=f"price${source}${symbol}", value=feed.model_dump_json())
        if not resp:
            logger.error(f"Failed to set price for {source}:{symbol}")
    for exchange in exchanges:
        await exchange.close()  # type: ignore
