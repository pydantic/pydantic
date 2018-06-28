import datetime
from decimal import Decimal
from enum import Enum
from types import GeneratorType
from uuid import UUID

from .main import BaseModel

__all__ = ['pydantic_encoder']


def isoformat(o):
    return o.isoformat()


ENCODERS_BY_TYPE = {
    UUID: str,
    datetime.datetime: isoformat,
    datetime.date: isoformat,
    datetime.time: isoformat,
    set: list,
    frozenset: list,
    GeneratorType: list,
    bytes: lambda o: o.decode(),
    Decimal: float,
}


def pydantic_encoder(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, Enum):
        return obj.value

    try:
        encoder = ENCODERS_BY_TYPE[type(obj)]
    except KeyError:
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")
    else:
        return encoder(obj)
