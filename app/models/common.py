from typing import List
from pydantic import BaseModel
from typing import Generic, TypeVar


M = TypeVar("M", bound=BaseModel)


class PageResponse(BaseModel, Generic[M]):
    items: List[M]
    total: int


class Pagination(BaseModel):
    limit: int
    skip: int
