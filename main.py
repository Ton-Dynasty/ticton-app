import asyncio
from enum import unique
import fastapi
import typer
from typer import Typer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from contextlib import asynccontextmanager
from app.providers import get_cache, get_db
from app.api import UserRouter, CoreRouter, AssetRouter
from dotenv import load_dotenv
from app.jobs import get_scheduler
from app.jobs.price import get_exchanges, set_price

from app.settings import get_settings


load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Put scheduler here to prevent local variable referenced before assignment error
    scheduler = get_scheduler()
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
        scheduler.add_job(set_price, "interval", seconds=3, args=[get_exchanges(), cache, manager])
        scheduler.start()
        yield
    finally:
        scheduler.shutdown()
        await manager.disconnect()
        await cache.disconnect()


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
app.include_router(UserRouter)
app.include_router(CoreRouter)
app.include_router(AssetRouter)


@cli.command(name="init")
def init():
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
        manager.db["users"].create_index("telegram_id", unique=True)
        manager.db["users"].create_index("wallet", unique=True)
        manager.db["pairs"].create_index({"base_asset_symbol": 1, "quote_asset_symbol": 1}, unique=True)

    typer.echo("Initializing database")
    asyncio.run(setup())


@cli.command(name="start")
def start_server(
    port: int = int(os.getenv("TICTON_SERVER_PORT", 8000)),
):
    typer.echo(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    cli()
