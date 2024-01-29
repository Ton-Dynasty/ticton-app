from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
from bson import ObjectId as _ObjectId


def check_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")
    return value


ObjectId = Annotated[str, AfterValidator(check_object_id)]
