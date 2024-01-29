import logging
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi import status, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from pytonconnect import TonConnect
from app.dao import DatabaseManager, get_db
from app.models.telegram import TelegramUser
from app.models.user import IUser, UserRegisterRequest, User
from app.api.middleware.auth import verify_tg_token
from app.utils import generate_tonproof_payload, verify_tonproof_payload
from app.settings import get_settings, Settings
from tonsdk.contract import Address

UserRouter = APIRouter(prefix="/user", tags=["user"])


@UserRouter.post(
    "/register",
    description="Register user with telegram auth headers and return ton proof url",
)
async def reigster(
    req: UserRegisterRequest,
    bg_tasks: BackgroundTasks,
    manager: DatabaseManager = Depends(get_db),
    tg_user: TelegramUser = Depends(verify_tg_token),
    settings: Settings = Depends(get_settings),
):
    try:
        # do not create user if their wallet address is already exists
        result = manager.db["users"].find_one({"telegram_id": tg_user.id})
        if result and result.get("telegram_id"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "User already exists"},
            )

        # generate proof
        proof_payload = generate_tonproof_payload(telegram_id=tg_user.id)

        connector = TonConnect(settings.TICTON_MANIFEST_URL)

        def status_changed(wallet_info):
            if wallet_info is not None:
                ok, payload = verify_tonproof_payload(proof_payload, wallet_info)
                if ok and payload is not None:
                    addr = Address(wallet_info.account.address).to_string(True, True)
                    u = IUser(
                        telegram_id=tg_user.id,
                        telegram_name=tg_user.username,
                        wallet=addr,
                    )
                    result = manager.db["users"].insert_one(u.model_dump())
                    print(f"User {payload.telegram_id} registered with address {addr}")

        def on_error(err):
            print("connect_error:", err)

        connector.on_status_change(status_changed, on_error)
        options = {app["app_name"]: app for app in connector.get_wallets()}
        wallet_type = options[req.wallet_type]
        generated_url = await connector.connect(
            wallet_type,
            {"ton_proof": proof_payload},
        )
        return JSONResponse(content={"url": generated_url}, status_code=status.HTTP_200_OK, background=bg_tasks)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)})


@UserRouter.get(
    "/{telegram_id}",
    response_model=User,
    description="Get user by telegram id",
)
async def get_user_by_id(manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError


@UserRouter.get("")
async def list_users(manager: DatabaseManager = Depends(get_db)):
    output = manager.db["users"].find()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(list(output)),
    )
