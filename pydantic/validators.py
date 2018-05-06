from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .exceptions import ConfigError, type_display

NoneType = type(None)


def display_as_type(v):
    return type_display(type(v))


def not_none_validator(v):
    if v is None:
        raise TypeError('None is not an allow value')
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
        raise TypeError(f'str or byte type expected not {display_as_type(v)}')


def bytes_validator(v) -> bytes:
    if isinstance(v, (bytes, NoneType)):
        return v
    return str_validator(v).encode()


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


def number_size_validator(v, field, config, **kwargs):
    min_size = getattr(field.type_, 'gt', config.min_number_size)
    if min_size is not None and v <= min_size:
        raise ValueError(f'size less than minimum allowed: {min_size}')

    max_size = getattr(field.type_, 'lt', config.max_number_size)
    if max_size is not None and v >= max_size:
        raise ValueError(f'size greater than maximum allowed: {max_size}')

    return v


def anystr_length_validator(v, field, config, **kwargs):
    v_len = len(v)

    min_length = getattr(field.type_, 'min_length', config.min_anystr_length)
    if min_length is not None and v_len < min_length:
        raise ValueError(f'length less than minimum allowed: {min_length}')

    max_length = getattr(field.type_, 'max_length', config.max_anystr_length)
    if max_length is not None and v_len > max_length:
        raise ValueError(f'length greater than maximum allowed: {max_length}')

    return v


def anystr_strip_whitespace(v, field, config, **kwargs):
    strip_whitespace = getattr(field.type_, 'strip_whitespace', config.anystr_strip_whitespace)
    if strip_whitespace:
        v = v.strip()

    return v


def ordered_dict_validator(v) -> OrderedDict:
    if isinstance(v, OrderedDict):
        return v
    return OrderedDict(v)


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v
    try:
        return dict(v)
    except TypeError as e:
        raise TypeError(f'value is not a valid dict, got {display_as_type(v)}') from e


def list_validator(v) -> list:
    if isinstance(v, list):
        return v
    return list(v)


def tuple_validator(v) -> tuple:
    if isinstance(v, tuple):
        return v
    return tuple(v)


def set_validator(v) -> set:
    if isinstance(v, set):
        return v
    return set(v)


def enum_validator(v, field, config, **kwargs) -> Enum:
    enum_v = field.type_(v)
    return enum_v.value if config.use_enum_values else enum_v


def uuid_validator(v, field, config, **kwargs) -> UUID:
    if isinstance(v, str):
        v = UUID(v)
    elif isinstance(v, (bytes, bytearray)):
        v = UUID(v.decode())
    elif not isinstance(v, UUID):
        raise ValueError(f'str, byte or native UUID type expected not {type(v)}')

    required_version = getattr(field.type_, '_required_version', None)
    if required_version and v.version != required_version:
        raise ValueError(f'uuid version {required_version} expected, not {v.version}')

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
        raise TypeError(f'value is not a valid decimal, got {display_as_type(v)}') from e

    if not v.is_finite():
        raise TypeError(f'value is not a valid decimal, got {display_as_type(v)}')

    return v


# order is important here, for example: bool is a subclass of int so has to come first, datetime before date same
_VALIDATORS = [
    (Enum, [enum_validator]),

    (str, [not_none_validator, str_validator, anystr_strip_whitespace, anystr_length_validator]),
    (bytes, [not_none_validator, bytes_validator, anystr_strip_whitespace, anystr_length_validator]),

    (bool, [bool_validator]),
    (int, [int, number_size_validator]),
    (float, [float, number_size_validator]),

    (Path, [Path]),

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
            raise TypeError(f'error checking inheritance of {type_!r} (type: {display_as_type(type_)})') from e
    raise ConfigError(f'no validator found for {type_}')
