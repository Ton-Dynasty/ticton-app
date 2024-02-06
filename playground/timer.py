import asyncio
from typing import Callable
from datetime import datetime

import ccxt.async_support as ccxt


def periodic(period: float):
    """
    Run async function periodically

    Parameters
    ----------
    period : float
        Period in seconds
    """

    def scheduler(func: Callable):
        async def wrapper(*args, **kwargs):
            task = None
            while True:
                try:
                    if task is None or task.done():
                        task = asyncio.create_task(func(*args, **kwargs))
                    else:
                        print(f"{datetime.now()} | {func.__name__} is already running, skipping...")
                    await asyncio.sleep(period)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Error in {func.__name__}: {e}")

        return wrapper

    return scheduler


@periodic(0.2)
async def hello(exchange: ccxt.Exchange, symbol: str = "TON/USDT"):
    ticker = await exchange.fetch_ticker(symbol)
    print(f"{symbol} | Bid {ticker['bid']} | Ask {ticker['ask']}")


async def main():
    exchange = ccxt.gateio()
    await hello(exchange)
    await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
