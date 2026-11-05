from __future__ import annotations as _annotations

import collections
import typing
from collections import Counter, OrderedDict, deque
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from fractions import Fraction
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from re import Pattern
from typing import Any
from uuid import UUID

from typing_extensions import TypedDict


@dataclass
class Row:
    field_type: type[Any] | str
    input_type: type[Any] | str
    python_input: bool = False
    json_input: bool = False
    strict: bool = False
    condition: str | None = None

    @property
    def field_type_str(self) -> str:
        return f'{self.field_type.__name__}' if hasattr(self.field_type, '__name__') else f'{self.field_type}'

    @property
    def input_type_str(self) -> str:
        return f'{self.input_type.__name__}' if hasattr(self.input_type, '__name__') else f'{self.input_type}'

    @property
    def input_source_str(self) -> str:
        if self.python_input:
            if self.json_input:
                return 'Python & JSON'
            else:
                return 'Python'
        elif self.json_input:
            return 'JSON'
        else:
            return ''


@dataclass
class ConversionTable:
    rows: list[Row]

    col_names = [
        'Field Type',
        'Input',
        'Strict',
        'Input Source',
        'Conditions',
    ]
    open_nowrap_span = '<span style="white-space: nowrap;">'
    close_nowrap_span = '</span>'

    def col_values(self, row: Row) -> list[str]:
        o = self.open_nowrap_span
        c = self.close_nowrap_span

        return [
            f'{o}`{row.field_type_str}`{c}',
            f'{o}`{row.input_type_str}`{c}',
            '✓' if row.strict else '',
            f'{o}{row.input_source_str}{c}',
            row.condition if row.condition else '',
        ]

    @staticmethod
    def row_as_markdown(cols: list[str]) -> str:
        return f'| {" | ".join(cols)} |'

    def as_markdown(self) -> str:
        lines = [self.row_as_markdown(self.col_names), self.row_as_markdown(['-'] * len(self.col_names))] + [
            self.row_as_markdown(self.col_values(row)) for row in self.rows
        ]
        return '\n'.join(lines)

    @staticmethod
    def row_sort_key(row: Row) -> Any:
        field_type = row.field_type_str or ' '
        input_type = row.input_type_str or ' '
        input_source = row.input_source_str

        # Include the .isupper() to make it so that leading-lowercase items come first
        return field_type[0].isupper(), field_type, input_type[0].isupper(), input_type, input_source

    def sorted(self) -> ConversionTable:
        return ConversionTable(sorted(self.rows, key=self.row_sort_key))

    def filtered(self, predicate: Callable[[Row], bool]) -> ConversionTable:
        return ConversionTable([row for row in self.rows if predicate(row)])


table_rows: list[Row] = [
    Row(
        str,
        str,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        str,
        bytes,
        python_input=True,
        condition='Assumes UTF-8, error on unicode decoding error.',
    ),
    Row(
        str,
        bytearray,
        python_input=True,
        condition='Assumes UTF-8, error on unicode decoding error.',
    ),
    Row(
        str,
        Enum,
        python_input=True,
        condition='Uses the value of the enum member.',
    ),
    Row(
        str,
        int,
        python_input=True,
        json_input=True,
        condition='Only if `coerce_numbers_to_str` is enabled.',
    ),
    Row(
        str,
        float,
        python_input=True,
        json_input=True,
        condition='Only if `coerce_numbers_to_str` is enabled.',
    ),
    Row(
        str,
        Decimal,
        python_input=True,
        condition='Only if `coerce_numbers_to_str` is enabled.',
    ),
    Row(
        bytes,
        bytes,
        strict=True,
        python_input=True,
    ),
    Row(
        bytes,
        str,
        strict=True,
        json_input=True,
        condition='Decoded according to the `val_json_bytes` setting (UTF-8 by default).',
    ),
    Row(
        bytes,
        str,
        python_input=True,
        condition='Decoded according to the `val_json_bytes` setting (UTF-8 by default).',
    ),
    Row(
        bytes,
        bytearray,
        python_input=True,
    ),
    Row(
        int,
        int,
        strict=True,
        python_input=True,
        json_input=True,
        condition='`bool` is explicitly forbidden.',
    ),
    Row(
        int,
        float,
        python_input=True,
        json_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`, raises error for `nan`, `inf`.',
    ),
    Row(
        int,
        Decimal,
        python_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`.',
    ),
    Row(
        int,
        bool,
        python_input=True,
        json_input=True,
    ),
    Row(
        int,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Must be a valid integer, e.g. `123`. Leading and trailing whitespace, underscores and a zero '
            'fractional part (e.g. `1.0`) are allowed.'
        ),
    ),
    Row(
        int,
        bytes,
        python_input=True,
        condition=(
            'Must be a valid integer, e.g. `123`. Leading and trailing whitespace, underscores and a zero '
            'fractional part (e.g. `1.0`) are allowed. Assumes UTF-8.'
        ),
    ),
    Row(
        int,
        Fraction,
        python_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`.',
    ),
    Row(
        int,
        Enum,
        python_input=True,
        condition='Uses the value of the enum member.',
    ),
    Row(
        float,
        float,
        strict=True,
        python_input=True,
        json_input=True,
        condition='`bool` is explicitly forbidden.',
    ),
    Row(
        float,
        int,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        float,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Must be a valid float, e.g. `3.141`, `1e3` or `inf`. Leading and trailing whitespace and underscores '
            'are allowed.'
        ),
    ),
    Row(
        float,
        bytes,
        python_input=True,
        condition=(
            'Must be a valid float, e.g. `3.141`, `1e3` or `inf`. Leading and trailing whitespace and underscores '
            'are allowed. Assumes UTF-8.'
        ),
    ),
    Row(
        float,
        Decimal,
        strict=True,
        python_input=True,
    ),
    Row(
        float,
        bool,
        python_input=True,
        json_input=True,
    ),
    Row(
        float,
        Fraction,
        strict=True,
        python_input=True,
    ),
    Row(
        float,
        Any,
        strict=True,
        python_input=True,
        condition='Must implement `__float__()` or `__index__()`.',
    ),
    Row(
        bool,
        bool,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        bool,
        int,
        python_input=True,
        json_input=True,
        condition='Allowed values: `0, 1`.',
    ),
    Row(
        bool,
        float,
        python_input=True,
        json_input=True,
        condition='Allowed values: `0.0, 1.0`.',
    ),
    Row(
        bool,
        Decimal,
        python_input=True,
        condition='Allowed values: `Decimal(0), Decimal(1)`.',
    ),
    Row(
        bool,
        str,
        python_input=True,
        json_input=True,
        condition=(
            "Case-insensitive. Allowed values: `'0'`, `'off'`, `'f'`, `'false'`, `'n'`, `'no'`, `'1'`, `'on'`, "
            "`'t'`, `'true'`, `'y'`, `'yes'`."
        ),
    ),
    Row(
        bool,
        bytes,
        python_input=True,
        condition='Same allowed values as for `str`. Assumes UTF-8.',
    ),
    Row(
        None,
        None,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        date,
        date,
        strict=True,
        python_input=True,
    ),
    Row(
        date,
        datetime,
        python_input=True,
        condition='Must be exact date, eg. no `H`, `M`, `S`, `f`.',
    ),
    Row(
        date,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Format: `YYYY-MM-DD`, a datetime with a zero time component, or a unix timestamp. Must be exact date. '
            'See [speedate](https://docs.rs/speedate/latest/speedate/).'
        ),
    ),
    Row(
        date,
        bytes,
        python_input=True,
        condition=(
            'Format: `YYYY-MM-DD`, a datetime with a zero time component, or a unix timestamp. Must be exact date. '
            'See [speedate](https://docs.rs/speedate/latest/speedate/). Assumes UTF-8.'
        ),
    ),
    Row(
        date,
        int,
        python_input=True,
        json_input=True,
        condition=(
            'Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting. Must '
            'be exact date.'
        ),
    ),
    Row(
        date,
        float,
        python_input=True,
        json_input=True,
        condition=(
            'Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting. Must '
            'be exact date.'
        ),
    ),
    Row(
        date,
        Decimal,
        python_input=True,
        condition=(
            'Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting. Must '
            'be exact date.'
        ),
    ),
    Row(
        date,
        str,
        strict=True,
        json_input=True,
        condition='Format: `YYYY-MM-DD`, or a unix timestamp. Must be exact date.',
    ),
    Row(
        datetime,
        datetime,
        strict=True,
        python_input=True,
    ),
    Row(
        datetime,
        date,
        python_input=True,
    ),
    Row(
        datetime,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Format: `YYYY-MM-DDTHH:MM:SS.f`, `YYYY-MM-DD`, or a unix timestamp. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/).'
        ),
    ),
    Row(
        datetime,
        bytes,
        python_input=True,
        condition=(
            'Format: `YYYY-MM-DDTHH:MM:SS.f`, `YYYY-MM-DD`, or a unix timestamp. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/). Assumes UTF-8.'
        ),
    ),
    Row(
        datetime,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting.',
    ),
    Row(
        datetime,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting.',
    ),
    Row(
        datetime,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds or milliseconds from epoch, depending on the `val_temporal_unit` setting.',
    ),
    Row(
        datetime,
        str,
        strict=True,
        json_input=True,
        condition=(
            'Format: `YYYY-MM-DDTHH:MM:SS.f`, or a unix timestamp. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/).'
        ),
    ),
    Row(
        time,
        time,
        strict=True,
        python_input=True,
    ),
    Row(
        time,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Format: `HH:MM[:SS[.FFFFFF]]`, with an optional timezone offset. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/).'
        ),
    ),
    Row(
        time,
        bytes,
        python_input=True,
        condition=(
            'Format: `HH:MM[:SS[.FFFFFF]]`, with an optional timezone offset. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/). Assumes UTF-8.'
        ),
    ),
    Row(
        time,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds, range `0 - 86399`.',
    ),
    Row(
        time,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds, range `0 - 86399.9*`.',
    ),
    Row(
        time,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds, range `0 - 86399.9*`.',
    ),
    Row(
        time,
        str,
        strict=True,
        json_input=True,
        condition=(
            'Format: `HH:MM[:SS[.FFFFFF]]`, with an optional timezone offset. See '
            '[speedate](https://docs.rs/speedate/latest/speedate/).'
        ),
    ),
    Row(
        timedelta,
        timedelta,
        strict=True,
        python_input=True,
    ),
    Row(
        timedelta,
        str,
        python_input=True,
        json_input=True,
        condition='Format: `ISO8601`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
    ),
    Row(
        timedelta,
        bytes,
        python_input=True,
        condition='Format: `ISO8601`. See [speedate](https://docs.rs/speedate/latest/speedate/), (UTF-8).',
    ),
    Row(
        timedelta,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds.',
    ),
    Row(
        timedelta,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds.',
    ),
    Row(
        timedelta,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds.',
    ),
    Row(
        timedelta,
        str,
        strict=True,
        json_input=True,
        condition='Format: `ISO8601`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
    ),
    Row(
        dict,
        dict,
        strict=True,
        python_input=True,
    ),
    Row(
        dict,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        dict,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        'frozendict',
        'frozendict',
        strict=True,
        python_input=True,
        condition='`frozendict` is only available in Python 3.15 and above.',
    ),
    Row(
        'frozendict',
        'Object',
        strict=True,
        json_input=True,
        condition='`frozendict` is only available in Python 3.15 and above.',
    ),
    Row(
        'frozendict',
        dict,
        python_input=True,
        condition='`frozendict` is only available in Python 3.15 and above.',
    ),
    Row(
        'frozendict',
        Mapping,
        python_input=True,
        condition=(
            '`frozendict` is only available in Python 3.15 and above. '
            'The input must implement the mapping interface and have an `items()` method.'
        ),
    ),
    Row(
        OrderedDict,
        OrderedDict,
        strict=True,
        python_input=True,
    ),
    Row(
        OrderedDict,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        OrderedDict,
        dict,
        python_input=True,
    ),
    Row(
        OrderedDict,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        Counter,
        Counter,
        strict=True,
        python_input=True,
    ),
    Row(
        Counter,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        Counter,
        dict,
        python_input=True,
    ),
    Row(
        Counter,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        TypedDict,
        dict,
        strict=True,
        python_input=True,
    ),
    Row(
        TypedDict,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        TypedDict,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        list,
        list,
        strict=True,
        python_input=True,
    ),
    Row(
        list,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        list,
        tuple,
        python_input=True,
    ),
    Row(
        list,
        set,
        python_input=True,
    ),
    Row(
        list,
        frozenset,
        python_input=True,
    ),
    Row(
        list,
        deque,
        python_input=True,
    ),
    Row(
        list,
        'dict_keys',
        python_input=True,
    ),
    Row(
        list,
        'dict_values',
        python_input=True,
    ),
    Row(
        list,
        Iterable,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        tuple,
        tuple,
        strict=True,
        python_input=True,
    ),
    Row(
        tuple,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        tuple,
        list,
        python_input=True,
    ),
    Row(
        tuple,
        set,
        python_input=True,
    ),
    Row(
        tuple,
        frozenset,
        python_input=True,
    ),
    Row(
        tuple,
        deque,
        python_input=True,
    ),
    Row(
        tuple,
        'dict_keys',
        python_input=True,
    ),
    Row(
        tuple,
        'dict_values',
        python_input=True,
    ),
    Row(
        tuple,
        Iterable,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        set,
        set,
        strict=True,
        python_input=True,
    ),
    Row(
        set,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        set,
        list,
        python_input=True,
    ),
    Row(
        set,
        tuple,
        python_input=True,
    ),
    Row(
        set,
        frozenset,
        python_input=True,
    ),
    Row(
        set,
        deque,
        python_input=True,
    ),
    Row(
        set,
        'dict_keys',
        python_input=True,
    ),
    Row(
        set,
        'dict_values',
        python_input=True,
    ),
    Row(
        set,
        Iterable,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        frozenset,
        frozenset,
        strict=True,
        python_input=True,
    ),
    Row(
        frozenset,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        frozenset,
        list,
        python_input=True,
    ),
    Row(
        frozenset,
        tuple,
        python_input=True,
    ),
    Row(
        frozenset,
        set,
        python_input=True,
    ),
    Row(
        frozenset,
        deque,
        python_input=True,
    ),
    Row(
        frozenset,
        'dict_keys',
        python_input=True,
    ),
    Row(
        frozenset,
        'dict_values',
        python_input=True,
    ),
    Row(
        frozenset,
        Iterable,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        'InstanceOf',
        Any,
        strict=True,
        python_input=True,
        condition='`isinstance()` check must return `True`.',
    ),
    Row(
        'InstanceOf',
        Any,
        strict=True,
        json_input=True,
        condition='Validated as the wrapped type.',
    ),
    Row(
        callable,
        Any,
        strict=True,
        python_input=True,
        condition='`callable()` check must return `True`.',
    ),
    Row(
        callable,
        '-',
        json_input=True,
        condition='Never valid.',
    ),
    Row(
        deque,
        deque,
        strict=True,
        python_input=True,
    ),
    Row(
        deque,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        deque,
        list,
        python_input=True,
    ),
    Row(
        deque,
        tuple,
        python_input=True,
    ),
    Row(
        deque,
        set,
        python_input=True,
    ),
    Row(
        deque,
        frozenset,
        python_input=True,
    ),
    Row(
        deque,
        Iterable,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        Any,
        Any,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        typing.NamedTuple,
        typing.NamedTuple,
        strict=True,
        python_input=True,
    ),
    Row(
        typing.NamedTuple,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        typing.NamedTuple,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        typing.NamedTuple,
        collections.namedtuple,
        strict=True,
        python_input=True,
    ),
    Row(
        typing.NamedTuple,
        tuple,
        strict=True,
        python_input=True,
    ),
    Row(
        typing.NamedTuple,
        list,
        strict=True,
        python_input=True,
    ),
    Row(
        typing.NamedTuple,
        dict,
        strict=True,
        python_input=True,
    ),
    Row(
        typing.NamedTuple,
        Iterable,
        strict=True,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        typing.NamedTuple,
        Mapping,
        strict=True,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        collections.namedtuple,
        collections.namedtuple,
        strict=True,
        python_input=True,
    ),
    Row(
        collections.namedtuple,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        collections.namedtuple,
        'Object',
        strict=True,
        json_input=True,
    ),
    Row(
        collections.namedtuple,
        typing.NamedTuple,
        strict=True,
        python_input=True,
    ),
    Row(
        collections.namedtuple,
        tuple,
        strict=True,
        python_input=True,
    ),
    Row(
        collections.namedtuple,
        list,
        strict=True,
        python_input=True,
    ),
    Row(
        collections.namedtuple,
        dict,
        strict=True,
        python_input=True,
    ),
    Row(
        collections.namedtuple,
        Iterable,
        strict=True,
        python_input=True,
        condition='Any iterable except `str`, `bytes`, `bytearray`, `dict` and mappings, e.g. generators.',
    ),
    Row(
        collections.namedtuple,
        Mapping,
        strict=True,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
    ),
    Row(
        Sequence,
        list,
        strict=True,
        python_input=True,
    ),
    Row(
        Sequence,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        Sequence,
        tuple,
        strict=True,
        python_input=True,
    ),
    Row(
        Sequence,
        deque,
        python_input=True,
    ),
    Row(
        Iterable,
        'Array',
        strict=True,
        json_input=True,
    ),
    Row(
        Iterable,
        Any,
        strict=True,
        python_input=True,
        condition='Any object for which `iter()` succeeds. Items are validated lazily.',
    ),
    Row(
        type,
        type,
        strict=True,
        python_input=True,
    ),
    Row(
        type,
        '-',
        json_input=True,
        condition='Never valid.',
    ),
    Row(
        Pattern,
        str,
        strict=True,
        python_input=True,
        json_input=True,
        condition='Input must be a valid pattern. Not valid for `Pattern[bytes]`.',
    ),
    Row(
        Pattern,
        bytes,
        strict=True,
        python_input=True,
        condition='Input must be a valid pattern. Not valid for `Pattern[str]`.',
    ),
    Row(
        Pattern,
        Pattern,
        strict=True,
        python_input=True,
        condition='The pattern type (`str` or `bytes`) must match.',
    ),
    Row(
        IPv4Address,
        IPv4Address,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv4Address,
        IPv4Interface,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv4Address,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        IPv4Address,
        str,
        python_input=True,
        json_input=True,
    ),
    Row(
        IPv4Address,
        bytes,
        python_input=True,
    ),
    Row(
        IPv4Address,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP address, must be less than `2**32`',
    ),
    Row(
        IPv4Interface,
        IPv4Interface,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv4Interface,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        IPv4Interface,
        IPv4Address,
        python_input=True,
    ),
    Row(
        IPv4Interface,
        str,
        python_input=True,
        json_input=True,
    ),
    Row(
        IPv4Interface,
        bytes,
        python_input=True,
    ),
    Row(
        IPv4Interface,
        tuple,
        python_input=True,
    ),
    Row(
        IPv4Interface,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP address, must be less than `2**32`',
    ),
    Row(
        IPv4Interface,
        IPv4Network,
        python_input=True,
    ),
    Row(
        IPv4Network,
        IPv4Network,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv4Network,
        str,
        strict=True,
        json_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv4Network,
        IPv4Address,
        python_input=True,
    ),
    Row(
        IPv4Network,
        IPv4Interface,
        python_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv4Network,
        str,
        python_input=True,
        json_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv4Network,
        bytes,
        python_input=True,
    ),
    Row(
        IPv4Network,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP network, must be less than `2**32`',
    ),
    Row(
        IPv4Network,
        tuple,
        python_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv6Address,
        IPv6Address,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv6Address,
        IPv6Interface,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv6Address,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        IPv6Address,
        str,
        python_input=True,
        json_input=True,
    ),
    Row(
        IPv6Address,
        bytes,
        python_input=True,
    ),
    Row(
        IPv6Address,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
    ),
    Row(
        IPv6Interface,
        IPv6Interface,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv6Interface,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        IPv6Interface,
        IPv6Address,
        python_input=True,
    ),
    Row(
        IPv6Interface,
        str,
        python_input=True,
        json_input=True,
    ),
    Row(
        IPv6Interface,
        bytes,
        python_input=True,
    ),
    Row(
        IPv6Interface,
        tuple,
        python_input=True,
    ),
    Row(
        IPv6Interface,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
    ),
    Row(
        IPv6Interface,
        IPv6Network,
        python_input=True,
    ),
    Row(
        IPv6Network,
        IPv6Network,
        strict=True,
        python_input=True,
    ),
    Row(
        IPv6Network,
        str,
        strict=True,
        json_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv6Network,
        IPv6Address,
        python_input=True,
    ),
    Row(
        IPv6Network,
        IPv6Interface,
        python_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv6Network,
        str,
        python_input=True,
        json_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        IPv6Network,
        bytes,
        python_input=True,
    ),
    Row(
        IPv6Network,
        int,
        python_input=True,
        json_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
    ),
    Row(
        IPv6Network,
        tuple,
        python_input=True,
        condition='Host bits must be zero.',
    ),
    Row(
        Enum,
        Enum,
        strict=True,
        python_input=True,
    ),
    Row(
        Enum,
        Any,
        strict=True,
        json_input=True,
        condition='Input value must be convertible to enum values.',
    ),
    Row(
        Enum,
        Any,
        python_input=True,
        condition='Input value must be convertible to enum values.',
    ),
    Row(
        IntEnum,
        IntEnum,
        strict=True,
        python_input=True,
    ),
    Row(
        IntEnum,
        Any,
        strict=True,
        json_input=True,
        condition='Input value must be one of the enum values, without type coercion.',
    ),
    Row(
        IntEnum,
        Any,
        python_input=True,
        condition='Input value must be convertible to enum values.',
    ),
    Row(
        Decimal,
        Decimal,
        strict=True,
        python_input=True,
    ),
    Row(
        Decimal,
        int,
        strict=True,
        json_input=True,
    ),
    Row(
        Decimal,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        Decimal,
        float,
        strict=True,
        json_input=True,
    ),
    Row(
        Decimal,
        int,
        python_input=True,
        json_input=True,
    ),
    Row(
        Decimal,
        str,
        python_input=True,
        json_input=True,
        condition=(
            'Must be a valid decimal, e.g. `3.141` or `1e3`. Leading and trailing whitespace and underscores are '
            'allowed.'
        ),
    ),
    Row(
        Decimal,
        float,
        python_input=True,
        json_input=True,
    ),
    Row(
        Decimal,
        tuple,
        python_input=True,
        condition='Decimal tuple form, e.g. `(0, (1, 4, 1), -2)`.',
    ),
    Row(
        Path,
        Path,
        strict=True,
        python_input=True,
    ),
    Row(
        Path,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        Path,
        str,
        python_input=True,
    ),
    Row(
        UUID,
        UUID,
        strict=True,
        python_input=True,
    ),
    Row(
        UUID,
        str,
        strict=True,
        json_input=True,
    ),
    Row(
        UUID,
        str,
        python_input=True,
    ),
    Row(
        UUID,
        bytes,
        python_input=True,
        condition='16 raw bytes, or a UTF-8 encoded UUID string.',
    ),
    Row(
        'ByteSize',
        str,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        'ByteSize',
        int,
        strict=True,
        python_input=True,
        json_input=True,
    ),
    Row(
        'ByteSize',
        float,
        python_input=True,
        json_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`.',
    ),
    Row(
        'ByteSize',
        Decimal,
        python_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`.',
    ),
    Row(
        complex,
        complex,
        strict=True,
        python_input=True,
    ),
    Row(
        complex,
        str,
        strict=True,
        json_input=True,
        condition='Must be a valid complex string, e.g. `1+2j`.',
    ),
    Row(
        complex,
        str,
        python_input=True,
        condition='Must be a valid complex string, e.g. `1+2j`.',
    ),
    Row(
        complex,
        int,
        python_input=True,
        json_input=True,
    ),
    Row(
        complex,
        float,
        python_input=True,
        json_input=True,
    ),
    Row(
        complex,
        Decimal,
        python_input=True,
    ),
    Row(
        Fraction,
        Fraction,
        strict=True,
        python_input=True,
    ),
    Row(
        Fraction,
        str,
        strict=True,
        json_input=True,
        condition='Must be a valid fraction, e.g. `1/3` or `0.5`.',
    ),
    Row(
        Fraction,
        int,
        strict=True,
        json_input=True,
    ),
    Row(
        Fraction,
        float,
        strict=True,
        json_input=True,
    ),
    Row(
        Fraction,
        str,
        python_input=True,
        condition='Must be a valid fraction, e.g. `1/3` or `0.5`.',
    ),
    Row(
        Fraction,
        int,
        python_input=True,
    ),
    Row(
        Fraction,
        float,
        python_input=True,
    ),
    Row(
        Fraction,
        Decimal,
        python_input=True,
    ),
    Row(
        'Literal',
        Any,
        strict=True,
        python_input=True,
        json_input=True,
        condition='Input must be equal to one of the literal values.',
    ),
    Row(
        Hashable,
        Any,
        strict=True,
        python_input=True,
        json_input=True,
        condition='`isinstance()` check against `Hashable` must return `True`.',
    ),
]

conversion_table = ConversionTable(table_rows).sorted()
