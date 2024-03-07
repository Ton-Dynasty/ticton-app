import asyncio
import fastapi
import typer
from typer import Typer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from contextlib import asynccontextmanager
from app.api.leaderboard import LeaderBoardRouter
from app.jobs.core import init_subscriptions
from app.providers import get_cache, get_db
from app.api import CoreRouter, AssetRouter
from dotenv import load_dotenv
from app.providers import get_scheduler
from app.jobs.price import get_exchanges, set_price
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from pytz import timezone
from app.settings import get_settings
from redis import StrictRedis
import time

os.environ["TZ"] = "Asia/Taipei"
time.tzset()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = None
    manager = None
    cache = None
    try:
        settings = get_settings()
        manager = await get_db()
        await manager.connect(
            host=settings.TICTON_DB_HOST,
            port=settings.TICTON_DB_PORT,
            username=settings.TICTON_DB_USERNAME,
            password=settings.TICTON_DB_PASSWORD,
            db_name=settings.TICTON_DB_NAME,
        )

        result = manager.db.command("ping")
        if result["ok"] != 1:
            raise Exception("Failed to connect to database")
        cache = await get_cache()
        await cache.connect(
            host=settings.TICTON_REDIS_HOST,
            port=settings.TICTON_REDIS_PORT,
            db=settings.TICTON_REDIS_DB,
            password=settings.TICTON_REDIS_PASSWORD,
        )
        resp = cache.client.ping()
        if not resp:
            raise Exception("Failed to connect to redis")
        scheduler = await get_scheduler()
        jobstores = {"default": MongoDBJobStore(client=manager.client)}
        job_defaults = {"coalesce": True}
        exchanges = get_exchanges()
        scheduler.scheduler.configure(jobstores=jobstores, job_defaults=job_defaults, timezone=timezone("Asia/Taipei"))
        if scheduler.scheduler.get_job("set_price") is None:
            scheduler.scheduler.add_job(set_price, "interval", seconds=3, args=[exchanges], id="set_price", name="set_price", replace_existing=True)
        await init_subscriptions(manager, scheduler)
        scheduler.scheduler.start()
        yield
    finally:
        if scheduler is not None:
            scheduler.scheduler.shutdown(wait=False)
        if manager is not None:
            await manager.disconnect()
        if cache is not None:
            await cache.disconnect()
        for exchange in exchanges:  # type: ignore
            await exchange.close()


cli = Typer()
app = FastAPI(
    title="Tic Ton web server",
    summary="Main web server for Tic Ton Oracle",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.dependency_overrides[get_db] = get_db
app.include_router(CoreRouter)
app.include_router(AssetRouter)
app.include_router(LeaderBoardRouter)


async def setup():
    settings = get_settings()
    manager = await get_db()
    await manager.connect(
        host=settings.TICTON_DB_HOST,
        port=settings.TICTON_DB_PORT,
        username=settings.TICTON_DB_USERNAME,
        password=settings.TICTON_DB_PASSWORD,
        db_name=settings.TICTON_DB_NAME,
    )
    # create indexes
    manager.db["pairs"].create_index("oracle_address", unique=True)
    manager.db["alarms"].create_index({"oracle": 1, "id": 1}, unique=True)


@cli.command(name="init")
def init():
    typer.echo("Initializing database")
    asyncio.run(setup())


@cli.command(name="start")
def start_server(
    port: int = int(os.getenv("TICTON_SERVER_PORT", 8000)),
):
    typer.echo("Initializing database")
    asyncio.run(setup())

    typer.echo(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    cli()
