import datetime
from decimal import Decimal
from enum import Enum
from types import GeneratorType
from typing import Any, Callable, Dict, Type, Union
from uuid import UUID

__all__ = 'pydantic_encoder', 'custom_pydantic_encoder', 'timedelta_isoformat'


def isoformat(o: Union[datetime.date, datetime.time]) -> str:
    return o.isoformat()


ENCODERS_BY_TYPE: Dict[Type[Any], Callable[[Any], Any]] = {
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


def pydantic_encoder(obj: Any) -> Any:
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


def custom_pydantic_encoder(type_encoders: Dict[Any, Callable[[Type[Any]], Any]], obj: Any) -> Any:
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
