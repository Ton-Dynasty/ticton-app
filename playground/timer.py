import asyncio
from typing import Callable
from datetime import datetime


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
            while True:
                asyncio.create_task(func(*args, **kwargs))
                await asyncio.sleep(period)

        return wrapper

    return scheduler


@periodic(2)
async def hello():
    print("Hello @", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    asyncio.run(hello())
