from __future__ import annotations as _annotations

import collections
import typing
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from re import Pattern
from typing import Any
from uuid import UUID

from pydantic_core import CoreSchema, core_schema
from typing_extensions import TypedDict

from pydantic import ByteSize, InstanceOf


@dataclass
class Row:
    field_type: type[Any] | str
    input_type: type[Any] | str
    python_input: bool = False
    json_input: bool = False
    strict: bool = False
    condition: str | None = None
    valid_examples: list[Any] | None = None
    invalid_examples: list[Any] | None = None
    core_schemas: list[type[CoreSchema]] | None = None

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
        lines = [self.row_as_markdown(self.col_names), self.row_as_markdown(['-'] * len(self.col_names))]
        for row in self.rows:
            lines.append(self.row_as_markdown(self.col_values(row)))
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

    def filtered(self, predicate: typing.Callable[[Row], bool]) -> ConversionTable:
        return ConversionTable([row for row in self.rows if predicate(row)])


table_rows: list[Row] = [
    Row(
        str,
        str,
        strict=True,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        str,
        bytes,
        python_input=True,
        condition='Assumes UTF-8, error on unicode decoding error.',
        valid_examples=[b'this is bytes'],
        invalid_examples=[b'\x81'],
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        str,
        bytearray,
        python_input=True,
        condition='Assumes UTF-8, error on unicode decoding error.',
        valid_examples=[bytearray(b'this is bytearray' * 3)],
        invalid_examples=[bytearray(b'\x81' * 5)],
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        bytes,
        bytes,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        str,
        strict=True,
        json_input=True,
        valid_examples=['foo'],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        str,
        python_input=True,
        valid_examples=['foo'],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        bytearray,
        python_input=True,
        valid_examples=[bytearray(b'this is bytearray' * 3)],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        int,
        int,
        strict=True,
        python_input=True,
        json_input=True,
        condition='`bool` is explicitly forbidden.',
        invalid_examples=[2**64, True, False],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        int,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        float,
        python_input=True,
        json_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`, raises error for `nan`, `inf`.',
        valid_examples=[2.0],
        invalid_examples=[2.1, 2.2250738585072011e308, float('nan'), float('inf')],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        Decimal,
        python_input=True,
        condition='Must be exact int, e.g. `val % 1 == 0`.',
        valid_examples=[Decimal(2.0)],
        invalid_examples=[Decimal(2.1)],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        bool,
        python_input=True,
        json_input=True,
        valid_examples=[True, False],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        str,
        python_input=True,
        json_input=True,
        condition='Must be numeric only, e.g. `[0-9]+`.',
        valid_examples=['123'],
        invalid_examples=['test', '123x'],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        bytes,
        python_input=True,
        condition='Must be numeric only, e.g. `[0-9]+`.',
        valid_examples=[b'123'],
        invalid_examples=[b'test', b'123x'],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        float,
        float,
        strict=True,
        python_input=True,
        json_input=True,
        condition='`bool` is explicitly forbidden.',
        invalid_examples=[True, False],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        int,
        strict=True,
        python_input=True,
        json_input=True,
        valid_examples=[123],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        str,
        python_input=True,
        json_input=True,
        condition='Must match `[0-9]+(\\.[0-9]+)?`.',
        valid_examples=['3.141'],
        invalid_examples=['test', '3.141x'],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        bytes,
        python_input=True,
        condition='Must match `[0-9]+(\\.[0-9]+)?`.',
        valid_examples=[b'3.141'],
        invalid_examples=[b'test', b'3.141x'],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        Decimal,
        python_input=True,
        valid_examples=[Decimal(3.5)],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        bool,
        python_input=True,
        json_input=True,
        valid_examples=[True, False],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        bool,
        bool,
        strict=True,
        python_input=True,
        json_input=True,
        valid_examples=[True, False],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        int,
        python_input=True,
        json_input=True,
        condition='Allowed values: `0, 1`.',
        valid_examples=[0, 1],
        invalid_examples=[2, 100],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        float,
        python_input=True,
        json_input=True,
        condition='Allowed values: `0.0, 1.0`.',
        valid_examples=[0.0, 1.0],
        invalid_examples=[2.0, 100.0],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        Decimal,
        python_input=True,
        condition='Allowed values: `Decimal(0), Decimal(1)`.',
        valid_examples=[Decimal(0), Decimal(1)],
        invalid_examples=[Decimal(2), Decimal(100)],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        str,
        python_input=True,
        json_input=True,
        condition=(
            "Allowed values: `'f'`, `'n'`, `'no'`, `'off'`, `'false'`, `'False'`, `'t'`, `'y'`, "
            "`'on'`, `'yes'`, `'true'`, `'True'`."
        ),
        valid_examples=['f', 'n', 'no', 'off', 'false', 'False', 't', 'y', 'on', 'yes', 'true', 'True'],
        invalid_examples=['test'],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        None,
        None,
        strict=True,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.NoneSchema],
    ),
    Row(
        date,
        date,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        datetime,
        python_input=True,
        condition='Must be exact date, eg. no `H`, `M`, `S`, `f`.',
        valid_examples=[datetime(2017, 5, 5)],
        invalid_examples=[datetime(2017, 5, 5, 10)],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        str,
        python_input=True,
        json_input=True,
        condition='Format: `YYYY-MM-DD`.',
        valid_examples=['2017-05-05'],
        invalid_examples=['2017-5-5', '2017/05/05'],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        bytes,
        python_input=True,
        condition='Format: `YYYY-MM-DD` (UTF-8).',
        valid_examples=[b'2017-05-05'],
        invalid_examples=[b'2017-5-5', b'2017/05/05'],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        int,
        python_input=True,
        json_input=True,
        condition=(
            'Interpreted as seconds or ms from epoch. '
            'See [speedate](https://docs.rs/speedate/latest/speedate/). Must be exact date.'
        ),
        valid_examples=[1493942400000, 1493942400],
        invalid_examples=[1493942401000],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        float,
        python_input=True,
        json_input=True,
        condition=(
            'Interpreted as seconds or ms from epoch. '
            'See [speedate](https://docs.rs/speedate/latest/speedate/). Must be exact date.'
        ),
        valid_examples=[1493942400000.0, 1493942400.0],
        invalid_examples=[1493942401000.0],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        Decimal,
        python_input=True,
        condition=(
            'Interpreted as seconds or ms from epoch. '
            'See [speedate](https://docs.rs/speedate/latest/speedate/). Must be exact date.'
        ),
        valid_examples=[Decimal(1493942400000), Decimal(1493942400)],
        invalid_examples=[Decimal(1493942401000)],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        datetime,
        datetime,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        date,
        python_input=True,
        valid_examples=[date(2017, 5, 5)],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        str,
        python_input=True,
        json_input=True,
        condition='Format: `YYYY-MM-DDTHH:MM:SS.f` or `YYYY-MM-DD`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=['2017-05-05 10:10:10', '2017-05-05T10:10:10.0002', '2017-05-05 10:10:10+00:00', '2017-05-05'],
        invalid_examples=['2017-5-5T10:10:10'],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        bytes,
        python_input=True,
        condition=(
            'Format: `YYYY-MM-DDTHH:MM:SS.f` or `YYYY-MM-DD`. See [speedate](https://docs.rs/speedate/latest/speedate/), (UTF-8).'
        ),
        valid_examples=[b'2017-05-05 10:10:10', b'2017-05-05T10:10:10.0002', b'2017-05-05 10:10:10+00:00'],
        invalid_examples=[b'2017-5-5T10:10:10'],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=[1493979010000, 1493979010],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=[1493979010000.0, 1493979010.0],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=[Decimal(1493979010000), Decimal(1493979010)],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        time,
        time,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        str,
        python_input=True,
        json_input=True,
        condition='Format: `HH:MM:SS.FFFFFF`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=['10:10:10.0002'],
        invalid_examples=['1:1:1'],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        bytes,
        python_input=True,
        condition='Format: `HH:MM:SS.FFFFFF`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=[b'10:10:10.0002'],
        invalid_examples=[b'1:1:1'],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds, range `0 - 86399`.',
        valid_examples=[3720],
        invalid_examples=[-1, 86400],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds, range `0 - 86399.9*`.',
        valid_examples=[3720.0002],
        invalid_examples=[-1.0, 86400.0],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds, range `0 - 86399.9*`.',
        valid_examples=[Decimal(3720.0002)],
        invalid_examples=[Decimal(-1), Decimal(86400)],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        timedelta,
        timedelta,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        str,
        python_input=True,
        json_input=True,
        condition='Format: `ISO8601`. See [speedate](https://docs.rs/speedate/latest/speedate/).',
        valid_examples=['1 days 10:10', '1 d 10:10'],
        invalid_examples=['1 10:10'],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        bytes,
        python_input=True,
        condition='Format: `ISO8601`. See [speedate](https://docs.rs/speedate/latest/speedate/), (UTF-8).',
        valid_examples=[b'1 days 10:10', b'1 d 10:10'],
        invalid_examples=[b'1 10:10'],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        int,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds.',
        valid_examples=[123_000],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        float,
        python_input=True,
        json_input=True,
        condition='Interpreted as seconds.',
        valid_examples=[123_000.0002],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        Decimal,
        python_input=True,
        condition='Interpreted as seconds.',
        valid_examples=[Decimal(123_000.0002)],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        dict,
        dict,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        dict,
        'Object',
        strict=True,
        json_input=True,
        valid_examples=['{"v": {"1": 1, "2": 2}}'],
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        dict,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
        valid_examples=[],
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        TypedDict,
        dict,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        'Object',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        Any,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        Mapping,
        python_input=True,
        condition='Must implement the mapping interface and have an `items()` method.',
        valid_examples=[],
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        list,
        list,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        tuple,
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        set,
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        frozenset,
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        deque,
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'dict_keys',
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'dict_values',
        python_input=True,
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        tuple,
        tuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        list,
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        set,
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        frozenset,
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        deque,
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        'dict_keys',
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        tuple,
        'dict_values',
        python_input=True,
        core_schemas=[core_schema.TupleSchema],
    ),
    Row(
        set,
        set,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        list,
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        tuple,
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        frozenset,
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        deque,
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'dict_keys',
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'dict_values',
        python_input=True,
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        frozenset,
        frozenset,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        list,
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        tuple,
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        set,
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        deque,
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'dict_keys',
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'dict_values',
        python_input=True,
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        InstanceOf,
        Any,
        strict=True,
        python_input=True,
        condition='`isinstance()` check must return `True`.',
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        InstanceOf,
        '-',
        json_input=True,
        condition='Never valid.',
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        callable,
        Any,
        strict=True,
        python_input=True,
        condition='`callable()` check must return `True`.',
        core_schemas=[core_schema.CallableSchema],
    ),
    Row(
        callable,
        '-',
        json_input=True,
        condition='Never valid.',
        core_schemas=[core_schema.CallableSchema],
    ),
    Row(
        deque,
        deque,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.WrapValidatorFunctionSchema],
    ),
    Row(
        deque,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.WrapValidatorFunctionSchema],
    ),
    Row(
        deque,
        list,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        deque,
        tuple,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        deque,
        set,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        deque,
        frozenset,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        Any,
        Any,
        strict=True,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.AnySchema],
    ),
    Row(
        typing.NamedTuple,
        typing.NamedTuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        typing.NamedTuple,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        typing.NamedTuple,
        collections.namedtuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        typing.NamedTuple,
        tuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        typing.NamedTuple,
        list,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        typing.NamedTuple,
        dict,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        collections.namedtuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        typing.NamedTuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        tuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        list,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        collections.namedtuple,
        dict,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CallSchema],
    ),
    Row(
        Sequence,
        list,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        Sequence,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        Sequence,
        tuple,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        Sequence,
        deque,
        python_input=True,
        core_schemas=[core_schema.ChainSchema],
    ),
    Row(
        Iterable,
        list,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        Iterable,
        'Array',
        strict=True,
        json_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        Iterable,
        tuple,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        Iterable,
        set,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        Iterable,
        frozenset,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        Iterable,
        deque,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.GeneratorSchema],
    ),
    Row(
        type,
        type,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsSubclassSchema],
    ),
    Row(
        Pattern,
        str,
        strict=True,
        python_input=True,
        json_input=True,
        condition='Input must be a valid pattern.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        Pattern,
        bytes,
        strict=True,
        python_input=True,
        condition='Input must be a valid pattern.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Address,
        IPv4Address,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv4Address,
        IPv4Interface,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv4Address,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv4Address,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Address,
        bytes,
        python_input=True,
        valid_examples=[b'\x00\x00\x00\x00'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Address,
        int,
        python_input=True,
        condition='integer representing the IP address, must be less than `2**32`',
        valid_examples=[168_430_090],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        IPv4Interface,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv4Interface,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        IPv4Address,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        bytes,
        python_input=True,
        valid_examples=[b'\xff\xff\xff\xff'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        tuple,
        python_input=True,
        valid_examples=[('192.168.0.1', '24')],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Interface,
        int,
        python_input=True,
        condition='integer representing the IP address, must be less than `2**32`',
        valid_examples=[168_430_090],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        IPv4Network,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv4Network,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        IPv4Address,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        IPv4Interface,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        bytes,
        python_input=True,
        valid_examples=[b'\xff\xff\xff\xff'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv4Network,
        int,
        python_input=True,
        condition='integer representing the IP network, must be less than `2**32`',
        valid_examples=[168_430_090],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Address,
        IPv6Address,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv6Address,
        IPv6Interface,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv6Address,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv6Address,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Address,
        bytes,
        python_input=True,
        valid_examples=[b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Address,
        int,
        python_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
        valid_examples=[340_282_366_920_938_463_463_374_607_431_768_211_455],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        IPv6Interface,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv6Interface,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        IPv6Address,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        bytes,
        python_input=True,
        valid_examples=[b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        tuple,
        python_input=True,
        valid_examples=[('2001:db00::1', '120')],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Interface,
        int,
        python_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
        valid_examples=[340_282_366_920_938_463_463_374_607_431_768_211_455],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        IPv6Network,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IPv6Network,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        IPv6Address,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        IPv6Interface,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        str,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        bytes,
        python_input=True,
        valid_examples=[b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IPv6Network,
        int,
        python_input=True,
        condition='integer representing the IP address, must be less than `2**128`',
        valid_examples=[340_282_366_920_938_463_463_374_607_431_768_211_455],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        Enum,
        Enum,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        Enum,
        Any,
        strict=True,
        json_input=True,
        condition='Input value must be convertible to enum values.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        Enum,
        Any,
        python_input=True,
        condition='Input value must be convertible to enum values.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IntEnum,
        IntEnum,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        IntEnum,
        Any,
        strict=True,
        json_input=True,
        condition='Input value must be convertible to enum values.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        IntEnum,
        Any,
        python_input=True,
        condition='Input value must be convertible to enum values.',
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        Decimal,
        Decimal,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.CustomErrorSchema],
    ),
    Row(
        Decimal,
        int,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.CustomErrorSchema],
    ),
    Row(
        Decimal,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.CustomErrorSchema],
    ),
    Row(
        Decimal,
        float,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.CustomErrorSchema],
    ),
    Row(
        Decimal,
        int,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        Decimal,
        str,
        python_input=True,
        json_input=True,
        condition='Must match `[0-9]+(\\.[0-9]+)?`.',
        valid_examples=['3.141'],
        invalid_examples=['test', '3.141x'],
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        Decimal,
        float,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        Path,
        Path,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        Path,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        Path,
        str,
        python_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        UUID,
        UUID,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        UUID,
        str,
        strict=True,
        json_input=True,
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        UUID,
        str,
        python_input=True,
        valid_examples=['{12345678-1234-5678-1234-567812345678}'],
        core_schemas=[core_schema.AfterValidatorFunctionSchema],
    ),
    Row(
        ByteSize,
        str,
        strict=True,
        python_input=True,
        json_input=True,
        valid_examples=['1.2', '1.5 KB', '6.2EiB'],
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        ByteSize,
        int,
        strict=True,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        ByteSize,
        float,
        strict=True,
        python_input=True,
        json_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
    Row(
        ByteSize,
        Decimal,
        strict=True,
        python_input=True,
        core_schemas=[core_schema.PlainValidatorFunctionSchema],
    ),
]

conversion_table = ConversionTable(table_rows).sorted()
