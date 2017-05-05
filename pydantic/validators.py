from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional

from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time

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


def number_size_validator(v, m):
    if m.config.min_number_size <= v <= m.config.max_number_size:
        return v
    raise ValueError(f'size not in range {m.config.min_number_size} to {m.config.max_number_size}')


def anystr_length_validator(v, m):
    if v is None or m.config.min_anystr_length <= len(v) <= m.config.max_anystr_length:
        return v
    raise ValueError(f'length not in range {m.config.max_anystr_length} to {m.config.max_anystr_length}')


def dict_validator(v) -> dict:
    if isinstance(v, dict):
        return v
    return dict(v)


VALIDATORS_LOOKUP = {
    int: [int, number_size_validator],
    float: [float, number_size_validator],
    bool: [bool_validator],

    Path: [Path],

    # TODO could do this better by detecting option Unions, removing not_none_validator and dealing with it directly
    Optional[str]: [str_validator, anystr_length_validator],
    str: [not_none_validator, str_validator, anystr_length_validator],

    Optional[bytes]: [bytes_validator, anystr_length_validator],
    bytes: [not_none_validator, bytes_validator, anystr_length_validator],

    dict: [not_none_validator, dict_validator],

    date: [parse_date],
    time: [parse_time],
    datetime: [parse_datetime],
    timedelta: [parse_duration],

    # TODO list, List, Dict, Union
}
