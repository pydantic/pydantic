from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from . import errors
from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .utils import change_exception, display_as_type, list_like

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
        return v.encode()
    elif isinstance(v, (float, int, Decimal)):
        return str(v).encode()
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

    with change_exception(errors.IntegerError, TypeError, ValueError):
        return int(v)


def float_validator(v) -> float:
    if isinstance(v, float):
        return v

    with change_exception(errors.FloatError, TypeError, ValueError):
        return float(v)


def number_size_validator(v, field, config, **kwargs):
    if field.type_.gt is not None and not v > field.type_.gt:
        raise errors.NumberNotGtError(limit_value=field.type_.gt)
    elif field.type_.ge is not None and not v >= field.type_.ge:
        raise errors.NumberNotGeError(limit_value=field.type_.ge)

    if field.type_.lt is not None and not v < field.type_.lt:
        raise errors.NumberNotLtError(limit_value=field.type_.lt)
    if field.type_.le is not None and not v <= field.type_.le:
        raise errors.NumberNotLeError(limit_value=field.type_.le)

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

    with change_exception(errors.DictError, TypeError, ValueError):
        return OrderedDict(v)


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v

    with change_exception(errors.DictError, TypeError, ValueError):
        return dict(v)


def list_validator(v) -> list:
    if isinstance(v, list):
        return v
    elif list_like(v):
        return list(v)
    else:
        raise errors.ListError()


def tuple_validator(v) -> tuple:
    if isinstance(v, tuple):
        return v
    elif list_like(v):
        return tuple(v)
    else:
        raise errors.TupleError()


def set_validator(v) -> set:
    if isinstance(v, set):
        return v
    elif list_like(v):
        return set(v)
    else:
        raise errors.SetError()


def enum_validator(v, field, config, **kwargs) -> Enum:
    with change_exception(errors.EnumError, ValueError):
        enum_v = field.type_(v)

    return enum_v.value if config.use_enum_values else enum_v


def uuid_validator(v, field, config, **kwargs) -> UUID:
    with change_exception(errors.UUIDError, ValueError):
        if isinstance(v, str):
            v = UUID(v)
        elif isinstance(v, (bytes, bytearray)):
            v = UUID(v.decode())

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

    with change_exception(errors.DecimalError, DecimalException):
        v = Decimal(v)

    if not v.is_finite():
        raise errors.DecimalIsNotFiniteError()

    return v


def path_validator(v) -> Path:
    if isinstance(v, Path):
        return v

    with change_exception(errors.PathError, TypeError):
        return Path(v)


def path_exists_validator(v) -> Path:
    if not v.exists():
        raise errors.PathNotExistsError(path=v)

    return v


def make_arbitrary_type_validator(type_):
    def arbitrary_type_validator(v) -> type_:
        if isinstance(v, type_):
            return v
        raise errors.ArbitraryTypeError(expected_arbitrary_type=type_)
    return arbitrary_type_validator


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


def find_validators(type_, arbitrary_types_allowed=False):
    if type_ is Any:
        return []

    supertype = _find_supertype(type_)
    if supertype is not None:
        type_ = supertype

    for val_type, validators in _VALIDATORS:
        try:
            if issubclass(type_, val_type):
                return validators
        except TypeError as e:
            raise RuntimeError(f'error checking inheritance of {type_!r} (type: {display_as_type(type_)})') from e

    if arbitrary_types_allowed:
        return [make_arbitrary_type_validator(type_)]
    else:
        raise RuntimeError(f'no validator found for {type_}')


def _find_supertype(type_):
    if not _is_new_type(type_):
        return None

    supertype = type_.__supertype__
    if _is_new_type(supertype):
        supertype = _find_supertype(supertype)

    return supertype


def _is_new_type(type_):
    return hasattr(type_, '__name__') and hasattr(type_, '__supertype__')
