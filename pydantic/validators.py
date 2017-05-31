from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .exceptions import ConfigError

NoneType = type(None)


def not_none_validator(v):
    if v is None:
        raise TypeError('None is not an allow value')
    return v


def str_validator(v) -> str:
    if isinstance(v, (str, NoneType)):
        return v
    elif isinstance(v, bytes):
        return v.decode()
    return str(v)


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


def number_size_validator(v, model, **kwargs):
    if model.config.min_number_size <= v <= model.config.max_number_size:
        return v
    raise ValueError(f'size not in range {model.config.min_number_size} to {model.config.max_number_size}')


def anystr_length_validator(v, model, **kwargs):
    if v is None or model.config.min_anystr_length <= len(v) <= model.config.max_anystr_length:
        return v
    raise ValueError(f'length not in range {model.config.max_anystr_length} to {model.config.max_anystr_length}')


def ordered_dict_validator(v) -> OrderedDict:
    if isinstance(v, OrderedDict):
        return v
    return OrderedDict(v)


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v
    return dict(v)


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


def enum_validator(v, field, **kwargs) -> Enum:
    return field.type_(v)


# order is important here, for example: bool is a subclass of int so has to come first, datetime before date same
_VALIDATORS = [
    (Enum, [enum_validator]),

    (str, [not_none_validator, str_validator, anystr_length_validator]),
    (bytes, [not_none_validator, bytes_validator, anystr_length_validator]),

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
]


def find_validators(type_):
    if type_ is Any:
        return []
    for val_type, validators in _VALIDATORS:
        if issubclass(type_, val_type):
            return validators
    raise ConfigError(f'no validator found for {type_}')
