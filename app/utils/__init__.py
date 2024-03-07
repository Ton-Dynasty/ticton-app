from datetime import datetime, timedelta
import json
from typing import Tuple, Optional, Annotated
from app.models.common import Pagination
from tonsdk.contract import Address
import hashlib
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder
from typing import Optional
from fastapi import Query


def get_pagination(page: Annotated[int, Query(ge=1)] = 1, per_page: Annotated[int, Query(ge=1, le=20)] = 10) -> Pagination:
    return Pagination(limit=per_page, skip=(page - 1) * per_page)


def calculate_time_elapse(ts: datetime) -> str:
    now = datetime.now()
    delta = now - ts
    if delta < timedelta(minutes=1):
        return f"{delta.seconds} seconds ago"
    if delta < timedelta(hours=1):
        return f"{delta.seconds // 60} mins ago"
    if delta < timedelta(days=1):
        return f"{delta.seconds // 3600} hours ago"
    return f"{delta.days} days ago"
