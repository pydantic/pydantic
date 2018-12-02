import datetime
from decimal import Decimal
from enum import Enum
from types import GeneratorType
from typing import Set
from uuid import UUID

__all__ = (
    'pydantic_encoder',
    'custom_pydantic_encoder',
    'timedelta_isoformat',
    'jsonable_encoder',
    'model_dict_jsonable',
)


def isoformat(o):
    return o.isoformat()


ENCODERS_BY_TYPE = {
    UUID: str,
    datetime.datetime: isoformat,
    datetime.date: isoformat,
    datetime.time: isoformat,
    datetime.timedelta: lambda td: td.total_seconds(),
    set: list,
    frozenset: list,
    GeneratorType: list,
    bytes: lambda o: o.decode(),
    Decimal: float,
}

JSONABLE_ENCODERS_BY_TYPE = ENCODERS_BY_TYPE.copy()
JSONABLE_ENCODERS_BY_TYPE.update({str: str, int: int, float: float, bool: bool, type(None): lambda n: n})
SEQUENCES = (list, set, frozenset, GeneratorType, tuple)


def pydantic_encoder(obj):
    from .main import BaseModel

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


def jsonable_encoder(obj):
    from .main import BaseModel

    if isinstance(obj, BaseModel):
        return model_dict_jsonable(obj)
    if isinstance(obj, Enum):
        return jsonable_encoder(obj.value)
    if isinstance(obj, dict):
        return {jsonable_encoder(key): jsonable_encoder(value) for key, value in obj.items()}
    if isinstance(obj, SEQUENCES):
        return [jsonable_encoder(item) for item in obj]
    try:
        encoder = JSONABLE_ENCODERS_BY_TYPE[type(obj)]
    except KeyError:
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not serializable")
    else:
        return encoder(obj)


def model_dict_jsonable(model, *, include: Set[str] = None, exclude: Set[str] = set(), by_alias: bool = False):
    model_dict = model.dict(include=include, exclude=exclude, by_alias=by_alias)
    return jsonable_encoder(model_dict)


def custom_pydantic_encoder(type_encoders, obj):
    encoder = type_encoders.get(type(obj))
    if encoder:
        return encoder(obj)
    else:
        return pydantic_encoder(obj)


def timedelta_isoformat(td: datetime.timedelta) -> str:
    """
    ISO 8601 encoding for timedeltas.
    """
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'P{td.days}DT{hours:d}H{minutes:d}M{seconds:d}.{td.microseconds:06d}S'
