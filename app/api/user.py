import logging
from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi import status, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from pytonconnect import TonConnect
from app.dao import DatabaseManager, get_db
from app.models.telegram import TelegramUser
from app.models.ton import TonProofReply
from app.models.user import IUser, User, WithdrawReqeuest
from app.api.middleware.auth import verify_tg_token
from app.utils import generate_tonproof_payload, verify_ton_proof
from app.settings import get_settings, Settings
from tonsdk.contract import Address
from datetime import datetime

UserRouter = APIRouter(prefix="/user", tags=["user"])


@UserRouter.post("/proof", description="Get ton proof payload")
async def get_proof(
    tg_user: TelegramUser = Depends(verify_tg_token),
    manager: DatabaseManager = Depends(get_db),
):
    try:
        # check if user is in database
        result = manager.db["users"].find_one({"telegram_id": tg_user.id})
        if result and result.get("telegram_id"):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "User already exists"})
        proof = generate_tonproof_payload(telegram_id=tg_user.id)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"proof": proof})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})


@UserRouter.post("/register", description="Register user by providing signed ton proof")
async def register_user(
    req: TonProofReply,
    tg_user: TelegramUser = Depends(verify_tg_token),
    manager: DatabaseManager = Depends(get_db),
):
    try:
        # check if user is in database
        result = manager.db["users"].find_one({"telegram_id": tg_user.id})
        if result and result.get("telegram_id"):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "User already exists"})
        # verify ton proof
        verified, payload, wallet = verify_ton_proof(req)
        if not verified or payload is None or wallet is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": "Failed to verify ton proof"})
        # check if id matches
        if payload.telegram_id != tg_user.id:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Telegram id mismatch"})
        # create user
        user = IUser(telegram_id=tg_user.id, telegram_name=tg_user.username, wallet=wallet.to_string(True))
        result = manager.db["users"].insert_one(user.model_dump())
        if not result:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Failed to register user"})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User registered successfully"})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})


@UserRouter.get(
    "/{telegram_id}",
    response_model=User,
    description="Get user by telegram id, balance field contains jettons, TON and reward token",
)
async def get_user_by_id(telegram_id: int, manager: DatabaseManager = Depends(get_db)):
    user = manager.db["users"].find_one({"telegram_id": telegram_id})
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "User not found"})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(User(**user)),
    )


@UserRouter.get("", response_model=List[User], description="List all users")
async def list_users(manager: DatabaseManager = Depends(get_db)):
    try:
        output = [User(**x) for x in manager.db["users"].find()]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(output),
        )
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(e)})


@UserRouter.get("/withdraw", description="withdraw user balance")
async def withdraw(req: WithdrawReqeuest, manager: DatabaseManager = Depends(get_db)):
    raise NotImplementedError
