import asyncio
import os
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi import status, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from pytonconnect import TonConnect
from app.dao import DatabaseManager, get_db
from app.models.telegram import TelegramUser
from app.models.user import UserRegister, User
from app.api.middleware.auth import verify_tg_token
from app.utils import generate_tonproof_payload, verify_tonproof_payload
from app.settings import get_settings, Settings

UserRouter = APIRouter(prefix="/user", tags=["user"])


@UserRouter.post(
    "", description="Register user with telegram auth headers and return ton proof url"
)
async def reigster(
    req: UserRegister,
    bg_tasks: BackgroundTasks,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
    settings: Settings = Depends(get_settings),
):
    if tg_user.isBot:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Bot cannot register"},
        )
    try:
        u = User(**tg_user.model_dump())

        # do not create user if their wallet address is already exists
        existed = manager.db["users"].find_one({"telegram_id": tg_user.id})
        if (
            existed.get("telegram_id") == tg_user.id
            and existed.get("wallet_address") is not None
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "User already exists"},
            )

        # create user
        manager.db["users"].insert_one(u.model_dump())

        # generate proof
        proof_payload = generate_tonproof_payload(telegram_id=tg_user.id)

        connector = TonConnect(settings.TICTON_MANIFEST_URL)

        def status_changed(wallet_info):
            if wallet_info is not None:
                verify_tonproof_payload(proof_payload, wallet_info)
            unsubscribe()  # type: ignore

        def on_error(err):
            print("connect_error:", err)

        connector.on_status_change(status_changed, on_error)
        options = connector.get_wallets()
        wallet_type = filter(lambda w: w["app_name"] == req.wallet_type, options)
        generated_url = await connector.connect(
            wallet_type,
            {"ton_proof": proof_payload},
        )

        async def wait_connected(conn: TonConnect, mng: DatabaseManager):
            for _ in range(120):
                await asyncio.sleep(1)
                if conn.connected:
                    if conn.account is not None:
                        # update user wallet address in mongodb
                        mng.db["users"].update_one(
                            {"telegram_id": tg_user.id},
                            {"$set": {"wallet_address": conn.account}},
                        )
                        break

        bg_tasks.add_task(wait_connected, conn=connector, mng=manager)

        return RedirectResponse(url=generated_url, background=bg_tasks)

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@UserRouter.get(
    "/{telegram_id}",
    response_model=User,
    description="Get user by telegram id",
)
async def get_user_by_id(manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError
