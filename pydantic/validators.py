from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from . import errors
from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .utils import display_as_type

NoneType = type(None)


def not_none_validator(v):
    if v is None:
        raise errors.NoneIsNotAllowedError()
    return v


def str_validator(v) -> str:
    if isinstance(v, (str, NoneType)):
        return v
    elif isinstance(v, (bytes, bytearray)):
        return v.decode()
    elif isinstance(v, (float, int, Decimal)):
        # is there anything else we want to add here? If you think so, create an issue.
        return str(v)
    else:
        raise errors.StrError()


def bytes_validator(v) -> bytes:
    if isinstance(v, bytes):
        return v
    elif isinstance(v, bytearray):
        return bytes(v)
    elif isinstance(v, str):
        return v.encode('utf-8')
    elif isinstance(v, (float, int, Decimal)):
        return str(v).encode('utf-8')
    else:
        raise errors.BytesError()


BOOL_STRINGS = {
    '1',
    'TRUE',
    'ON',
    'YES',
}


def bool_validator(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, bytes):
        v = v.decode()
    if isinstance(v, str):
        return v.upper() in BOOL_STRINGS
    return bool(v)


def int_validator(v) -> int:
    if isinstance(v, int):
        return v

    try:
        v = int(v)
    except (TypeError, ValueError) as e:
        raise errors.IntegerError() from e

    return v


def float_validator(v) -> float:
    if isinstance(v, float):
        return v

    try:
        v = float(v)
    except (TypeError, ValueError) as e:
        raise errors.FloatError() from e

    return v


def number_size_validator(v, field, config, **kwargs):
    if field.type_.gt is not None and v < field.type_.gt:
        raise errors.NumberMinSizeError(limit_value=field.type_.gt)

    if field.type_.lt is not None and v > field.type_.lt:
        raise errors.NumberMaxSizeError(limit_value=field.type_.lt)

    return v


def anystr_length_validator(v, field, config, **kwargs):
    v_len = len(v)

    min_length = getattr(field.type_, 'min_length', config.min_anystr_length)
    if min_length is not None and v_len < min_length:
        raise errors.AnyStrMinLengthError(limit_value=min_length)

    max_length = getattr(field.type_, 'max_length', config.max_anystr_length)
    if max_length is not None and v_len > max_length:
        raise errors.AnyStrMaxLengthError(limit_value=max_length)

    return v


def anystr_strip_whitespace(v, field, config, **kwargs):
    strip_whitespace = getattr(field.type_, 'strip_whitespace', config.anystr_strip_whitespace)
    if strip_whitespace:
        v = v.strip()

    return v


def ordered_dict_validator(v) -> OrderedDict:
    if isinstance(v, OrderedDict):
        return v

    try:
        v = OrderedDict(v)
    except (TypeError, ValueError) as e:
        raise errors.DictError() from e

    return v


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v

    try:
        v = dict(v)
    except (TypeError, ValueError) as e:
        raise errors.DictError() from e

    return v


def list_validator(v) -> list:
    if isinstance(v, list):
        return v

    try:
        v = list(v)
    except TypeError as e:
        raise errors.ListError() from e

    return v


def tuple_validator(v) -> tuple:
    if isinstance(v, tuple):
        return v

    try:
        v = tuple(v)
    except TypeError as e:
        raise errors.TupleError() from e

    return v


def set_validator(v) -> set:
    if isinstance(v, set):
        return v

    try:
        v = set(v)
    except TypeError as e:
        raise errors.SetError() from e

    return v


def enum_validator(v, field, config, **kwargs) -> Enum:
    try:
        enum_v = field.type_(v)
    except ValueError as e:
        raise errors.EnumError() from e

    return enum_v.value if config.use_enum_values else enum_v


def uuid_validator(v, field, config, **kwargs) -> UUID:
    try:
        if isinstance(v, str):
            v = UUID(v)
        elif isinstance(v, (bytes, bytearray)):
            v = UUID(v.decode())
    except ValueError as e:
        raise errors.UUIDError() from e

    if not isinstance(v, UUID):
        raise errors.UUIDError()

    required_version = getattr(field.type_, '_required_version', None)
    if required_version and v.version != required_version:
        raise errors.UUIDVersionError(required_version=required_version)

    return v


def decimal_validator(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    elif isinstance(v, (bytes, bytearray)):
        v = v.decode()

    v = str(v).strip()

    try:
        v = Decimal(v)
    except DecimalException as e:
        raise errors.DecimalError() from e

    if not v.is_finite():
        raise errors.DecimalIsNotFiniteError()

    return v


def path_validator(v) -> Path:
    if isinstance(v, Path):
        return v

    try:
        v = Path(v)
    except TypeError as e:
        raise errors.PathError() from e

    return v


# order is important here, for example: bool is a subclass of int so has to come first, datetime before date same
_VALIDATORS = [
    (Enum, [enum_validator]),

    (str, [not_none_validator, str_validator, anystr_strip_whitespace, anystr_length_validator]),
    (bytes, [not_none_validator, bytes_validator, anystr_strip_whitespace, anystr_length_validator]),

    (bool, [bool_validator]),
    (int, [int_validator]),
    (float, [float_validator]),

    (Path, [path_validator]),

    (datetime, [parse_datetime]),
    (date, [parse_date]),
    (time, [parse_time]),
    (timedelta, [parse_duration]),

    (OrderedDict, [ordered_dict_validator]),
    (dict, [dict_validator]),
    (list, [list_validator]),
    (tuple, [tuple_validator]),
    (set, [set_validator]),
    (UUID, [not_none_validator, uuid_validator]),
    (Decimal, [not_none_validator, decimal_validator]),
]


def find_validators(type_):
    if type_ is Any:
        return []
    for val_type, validators in _VALIDATORS:
        try:
            if issubclass(type_, val_type):
                return validators
        except TypeError as e:
            raise RuntimeError(f'error checking inheritance of {type_!r} (type: {display_as_type(type_)})') from e
    raise errors.ConfigError(f'no validator found for {type_}')
