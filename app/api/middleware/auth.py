import json
import os
import hmac
import hashlib
from fastapi import Header, HTTPException, Depends
from app.models.telegram import TelegramUser
from app.settings import get_settings, Settings


async def verify_tg_token(
    x_auth_date: int = Header(...),
    x_query_id: str = Header(...),
    x_user: str = Header(...),
    x_hash: str = Header(...),
    settings: Settings = Depends(get_settings),
):
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
    bot_token = settings.TICTON_TG_BOT_TOKEN
    data_check_string = f"auth_date={x_auth_date}\nquery_id={x_query_id}\nuser={x_user}"
    secret_key = hmac.new(
        bytes("WebAppData", "utf-8"), bytes(bot_token, "utf-8"), hashlib.sha256
    )
    _hash = hmac.new(
        secret_key.digest(), bytes(data_check_string, "utf-8"), hashlib.sha256
    ).hexdigest()
    if _hash != x_hash:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return TelegramUser(**json.loads(x_user))
