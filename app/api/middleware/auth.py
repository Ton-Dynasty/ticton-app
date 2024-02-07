import json
import hmac
import hashlib
from fastapi import Header, HTTPException, Depends, status
from app.models.telegram import TelegramUser
from app.settings import get_settings, Settings
from typing import Annotated, Optional
from urllib.parse import unquote


async def verify_tg_token(
    x_hash: Annotated[Optional[str], Header()] = None,
    authorization: Annotated[Optional[str], Header()] = None,
    settings: Settings = Depends(get_settings),
) -> TelegramUser:
    """
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    ```python
    datacheck_string="auth_date=<auth_date>\\nquery_id=<query_id>\\nuser=<user>"
    ```

    ```python
    secret_key = HMAC_SHA256(<bot_token>, "WebAppData")
    if (hex(HMAC_SHA256(data_check_string, secret_key)) == hash) {
        // data is from Telegram
    }
    ```

    auth_date: Unix time when the login page was opened.
    query_id: Unique query identifier.
    user: User identifier, json string.
    hash: Hash for the authorization token.
    """
    if settings.TICTON_MODE == "dev":
        return TelegramUser(
            allows_write_to_pm=True,
            first_name="Test",
            id=123456789,
            is_premium=None,
            language_code="zh-TW",
            last_name="Test",
            username="Test",
        )
    try:
        tma = authorization.split(" ")
        if len(tma) != 2:
            print("Authorization header is not valid")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Header is not valid")
        bot_token = settings.TICTON_TG_BOT_TOKEN
        if tma[0] != "tma":
            print("Authorization header should start with tma")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header should start with tma")
        init_data = unquote(tma[1])
        init_data_sorted = sorted(
            [chunk.split("=") for chunk in init_data.split("&") if chunk[: len("hash=")] != "hash="],
            key=lambda x: x[0],
        )
        init_data_sorted = "\n".join([f"{rec[0]}={rec[1]}" for rec in init_data_sorted])
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        data_check = hmac.new(secret_key, init_data_sorted.encode(), hashlib.sha256)
        if data_check.hexdigest() != x_hash:
            print("Hash is not valid")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hash is not valid")
        init_data_dict = dict([chunk.split("=") for chunk in init_data.split("&")])
        user = json.loads(init_data_dict["user"])
        return TelegramUser(**user)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
