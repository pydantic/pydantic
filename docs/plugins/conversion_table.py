from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Literal, Mapping

from pydantic_core import CoreSchema, core_schema
from typing_extensions import TypedDict

# TODO: List of missing types
# deque
# typing.Any
# typing.NamedTuple
# collections.namedtuple
# typing.Sequence
# typing.Iterable
# typing.Type
# typing.Pattern
# ipaddress.IPv4Address
# ipaddress.IPv4Interface
# ipaddress.IPv4Network
# ipaddress.IPv6Address
# ipaddress.IPv6Interface
# ipaddress.IPv6Network
# enum.Enum
# enum.IntEnum
# decimal.Decimal
# pathlib.Path
# uuid.UUID
# ByteSize


@dataclass
class Row:
    field_type: type[Any]
    input_type: type[Any]
    mode: Literal['lax', 'strict']
    input_format: Literal['python', 'JSON', 'python & JSON']
    condition: str | None = None
    valid_examples: list[Any] | None = None
    invalid_examples: list[Any] | None = None
    core_schemas: list[type[CoreSchema]] | None = None


table: list[Row] = [
    Row(
        str,
        str,
        'strict',
        'python & JSON',
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        str,
        bytes,
        'lax',
        'python',
        condition='assumes UTF-8, error on unicode decoding error',
        valid_examples=[b'this is bytes'],
        invalid_examples=[b'\x81'],
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        str,
        bytearray,
        'lax',
        'python',
        condition='assumes UTF-8, error on unicode decoding error',
        valid_examples=[bytearray(b'this is bytearray' * 3)],
        invalid_examples=[bytearray(b'\x81' * 5)],
        core_schemas=[core_schema.StringSchema],
    ),
    Row(
        bytes,
        bytes,
        'strict',
        'python',
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        str,
        'strict',
        'JSON',
        valid_examples=['foo'],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        str,
        'lax',
        'python',
        valid_examples=['foo'],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        bytes,
        bytearray,
        'lax',
        'python',
        valid_examples=[bytearray(b'this is bytearray' * 3)],
        core_schemas=[core_schema.BytesSchema],
    ),
    Row(
        int,
        int,
        'strict',
        'python & JSON',
        condition='max abs value `2^64` - `i64` is used internally, `bool` explicitly forbidden',
        invalid_examples=[2**64, True, False],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        int,
        'lax',
        'python & JSON',
        condition='`i64`. Limits `numbers > (2 ^ 63) - 1` to `(2 ^ 63) - 1`',
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        float,
        'lax',
        'python & JSON',
        condition='`i64`, must be exact int, e.g. `val % 1 == 0`, `nan`, `inf` raise errors',
        valid_examples=[2.0],
        invalid_examples=[2.1, 2.2250738585072011e308, float('nan'), float('inf')],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        Decimal,
        'lax',
        'python',
        condition='`i64`, must be exact int, e.g. `val % 1 == 0`',
        valid_examples=[Decimal(2.0)],
        invalid_examples=[Decimal(2.1)],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        bool,
        'lax',
        'python & JSON',
        valid_examples=[True, False],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        str,
        'lax',
        'python & JSON',
        condition='`i64`, must be numeric only, e.g. `[0-9]+`',
        valid_examples=['123'],
        invalid_examples=['test'],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        int,
        bytes,
        'lax',
        'python',
        condition='`i64`, must be numeric only, e.g. `[0-9]+`',
        valid_examples=[b'123'],
        invalid_examples=[b'test'],
        core_schemas=[core_schema.IntSchema],
    ),
    Row(
        float,
        float,
        'strict',
        'python & JSON',
        condition='`bool` explicitly forbidden',
        invalid_examples=[True, False],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        int,
        'strict',
        'python & JSON',
        valid_examples=[123],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        str,
        'lax',
        'python & JSON',
        condition='must match `[0-9]+(\\.[0-9]+)?`',
        valid_examples=['3.141'],
        invalid_examples=['test'],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        bytes,
        'lax',
        'python',
        condition='must match `[0-9]+(\\.[0-9]+)?`',
        valid_examples=[b'3.141'],
        invalid_examples=[b'test'],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        Decimal,
        'lax',
        'python',
        valid_examples=[Decimal(3.5)],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        float,
        bool,
        'lax',
        'python & JSON',
        valid_examples=[True, False],
        core_schemas=[core_schema.FloatSchema],
    ),
    Row(
        bool,
        bool,
        'strict',
        'python & JSON',
        valid_examples=[True, False],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        int,
        'lax',
        'python & JSON',
        condition='allowed: `0, 1`',
        valid_examples=[0, 1],
        invalid_examples=[2, 100],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        float,
        'lax',
        'python & JSON',
        condition='allowed: `0.0, 1.0`',
        valid_examples=[0.0, 1.0],
        invalid_examples=[2.0, 100.0],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        Decimal,
        'lax',
        'python',
        condition='allowed: `Decimal(0), Decimal(1)`',
        valid_examples=[Decimal(0), Decimal(1)],
        invalid_examples=[Decimal(2), Decimal(100)],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        bool,
        str,
        'lax',
        'python & JSON',
        condition="allowed: `'f'`, `'n'`, `'no'`, `'off'`, `'false'`, `'t'`, `'y'`, `'on'`, `'yes'`, `'true'`",
        valid_examples=['f', 'n', 'no', 'off', 'false', 't', 'y', 'on', 'yes', 'true'],
        invalid_examples=['test'],
        core_schemas=[core_schema.BoolSchema],
    ),
    Row(
        None,
        None,
        'stric',
        'python & JSON',
        core_schemas=[core_schema.NoneSchema],
    ),
    Row(
        date,
        date,
        'stric',
        'python',
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        datetime,
        'lax',
        'python',
        condition='must be exact date, eg. no H, M, S, f',
        valid_examples=[datetime(2017, 5, 5)],
        invalid_examples=[datetime(2017, 5, 5, 10)],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        str,
        'strict',
        'JSON',
        condition='format `YYYY-MM-DD`',
        valid_examples=['2017-05-05'],
        invalid_examples=['2017-5-5', '2017/05/05'],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        str,
        'lax',
        'python',
        condition='format `YYYY-MM-DD`',
        valid_examples=['2017-05-05'],
        invalid_examples=['2017-5-5', '2017/05/05'],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        bytes,
        'lax',
        'python',
        condition='format `YYYY-MM-DD` (UTF-8)',
        valid_examples=[b'2017-05-05'],
        invalid_examples=[b'2017-5-5', b'2017/05/05'],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        int,
        'lax',
        'python & JSON',
        condition=(
            'interpreted as seconds or ms from epoch, '
            'see [speedate](https://docs.rs/speedate/latest/speedate/), must be exact date'
        ),
        valid_examples=[1493942400000, 1493942400],
        invalid_examples=[1493942401000],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        float,
        'lax',
        'python & JSON',
        condition=(
            'interpreted as seconds or ms from epoch, '
            'see [speedate](https://docs.rs/speedate/latest/speedate/), must be exact date'
        ),
        valid_examples=[1493942400000.0, 1493942400.0],
        invalid_examples=[1493942401000.0],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        date,
        Decimal,
        'lax',
        'python',
        condition=(
            'interpreted as seconds or ms from epoch, '
            'see [speedate](https://docs.rs/speedate/latest/speedate/), must be exact date'
        ),
        valid_examples=[Decimal(1493942400000), Decimal(1493942400)],
        invalid_examples=[Decimal(1493942401000)],
        core_schemas=[core_schema.DateSchema],
    ),
    Row(
        datetime,
        datetime,
        'stric',
        'python',
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        date,
        'lax',
        'python',
        valid_examples=[date(2017, 5, 5)],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        str,
        'strict',
        'JSON',
        condition='format YYYY-MM-DDTHH:MM:SS.f etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['2017-05-05 10:10:10', '2017-05-05T10:10:10.0002', '2017-05-05 10:10:10+00:00'],
        invalid_examples=['2017-5-5T10:10:10'],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        str,
        'lax',
        'python',
        condition='format YYYY-MM-DDTHH:MM:SS.f etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['2017-05-05 10:10:10', '2017-05-05T10:10:10.0002', '2017-05-05 10:10:10+00:00'],
        invalid_examples=['2017-5-5T10:10:10'],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        bytes,
        'lax',
        'python',
        condition=(
            'format YYYY-MM-DDTHH:MM:SS.f etc. see [speedate](https://docs.rs/speedate/latest/speedate/), (UTF-8)'
        ),
        valid_examples=[b'2017-05-05 10:10:10', b'2017-05-05T10:10:10.0002', b'2017-05-05 10:10:10+00:00'],
        invalid_examples=[b'2017-5-5T10:10:10'],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        int,
        'lax',
        'python & JSON',
        condition='interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=[1493979010000, 1493979010],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        float,
        'lax',
        'python & JSON',
        condition='interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=[1493979010000.0, 1493979010.0],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        datetime,
        Decimal,
        'lax',
        'python',
        condition='interpreted as seconds or ms from epoch, see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=[Decimal(1493979010000), Decimal(1493979010)],
        core_schemas=[core_schema.DatetimeSchema],
    ),
    Row(
        time,
        time,
        'strict',
        'python',
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        str,
        'strict',
        'JSON',
        condition='format HH:MM:SS.FFFFFF etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['10:10:10.0002'],
        invalid_examples=['1:1:1'],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        str,
        'lax',
        'python',
        condition='format HH:MM:SS.FFFFFF etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['10:10:10.0002'],
        invalid_examples=['1:1:1'],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        bytes,
        'lax',
        'python',
        condition='format HH:MM:SS.FFFFFF etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=[b'10:10:10.0002'],
        invalid_examples=[b'1:1:1'],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        int,
        'lax',
        'python & JSON',
        condition='interpreted as seconds, range `0 - 86399`',
        valid_examples=[3720],
        invalid_examples=[-1, 86400],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        float,
        'lax',
        'python & JSON',
        condition='interpreted as seconds, range `0 - 86399.9*`',
        valid_examples=[3720.0002],
        invalid_examples=[-1.0, 86400.0],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        time,
        Decimal,
        'lax',
        'python',
        condition='interpreted as seconds, range `0 - 86399.9*`',
        valid_examples=[Decimal(3720.0002)],
        invalid_examples=[Decimal(-1), Decimal(86400)],
        core_schemas=[core_schema.TimeSchema],
    ),
    Row(
        timedelta,
        timedelta,
        'strict',
        'python',
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        str,
        'strict',
        'JSON',
        condition='format ISO8601 etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['1 days 10:10', '1 d 10:10'],
        invalid_examples=['1 10:10'],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        str,
        'lax',
        'python',
        condition='format ISO8601 etc. see [speedate](https://docs.rs/speedate/latest/speedate/)',
        valid_examples=['1 days 10:10', '1 d 10:10'],
        invalid_examples=['1 10:10'],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        bytes,
        'lax',
        'python',
        condition='format ISO8601 etc. see [speedate](https://docs.rs/speedate/latest/speedate/), (UTF-8)',
        valid_examples=[b'1 days 10:10', b'1 d 10:10'],
        invalid_examples=[b'1 10:10'],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        int,
        'lax',
        'python & JSON',
        condition='interpreted as seconds',
        valid_examples=[123_000],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        float,
        'lax',
        'python & JSON',
        condition='interpreted as seconds',
        valid_examples=[123_000.0002],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        timedelta,
        Decimal,
        'lax',
        'python',
        condition='interpreted as seconds',
        valid_examples=[Decimal(123_000.0002)],
        core_schemas=[core_schema.TimedeltaSchema],
    ),
    Row(
        dict,
        dict,
        'strict',
        'python',
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        dict,
        'Object',
        'strict',
        'JSON',
        valid_examples=['{"v": {"1": 1, "2": 2}}'],
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        dict,
        Mapping,
        'lax',
        'python',
        condition='must implement the mapping interface and have an `items()` method',
        valid_examples=[],
        core_schemas=[core_schema.DictSchema],
    ),
    Row(
        TypedDict,
        dict,
        'strict',
        'python',
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        'Object',
        'strict',
        'JSON',
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        Any,
        'strict',
        'python',
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        TypedDict,
        Mapping,
        'lax',
        'python',
        condition='must implement the mapping interface and have an `items()` method',
        valid_examples=[],
        core_schemas=[core_schema.TypedDictSchema],
    ),
    Row(
        list,
        list,
        'strict',
        'python',
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'Array',
        'strict',
        'JSON',
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        tuple,
        'lax',
        'python',
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'dict_keys',
        'lax',
        'python',
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        list,
        'dict_values',
        'lax',
        'python',
        core_schemas=[core_schema.ListSchema],
    ),
    Row(
        tuple,
        tuple,
        'strict',
        'python',
        core_schemas=[core_schema.TuplePositionalSchema, core_schema.TupleVariableSchema],
    ),
    Row(
        tuple,
        'Array',
        'strict',
        'JSON',
        core_schemas=[core_schema.TuplePositionalSchema, core_schema.TupleVariableSchema],
    ),
    Row(
        tuple,
        list,
        'lax',
        'python',
        core_schemas=[core_schema.TuplePositionalSchema, core_schema.TupleVariableSchema],
    ),
    Row(
        tuple,
        'dict_keys',
        'lax',
        'python',
        core_schemas=[core_schema.TuplePositionalSchema, core_schema.TupleVariableSchema],
    ),
    Row(
        tuple,
        'dict_values',
        'lax',
        'python',
        core_schemas=[core_schema.TuplePositionalSchema, core_schema.TupleVariableSchema],
    ),
    Row(
        set,
        set,
        'strict',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'Array',
        'strict',
        'JSON',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        list,
        'lax',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        tuple,
        'lax',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        frozenset,
        'lax',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'dict_keys',
        'lax',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        set,
        'dict_values',
        'lax',
        'python',
        core_schemas=[core_schema.SetSchema],
    ),
    Row(
        frozenset,
        frozenset,
        'strict',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'Array',
        'strict',
        'JSON',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        list,
        'lax',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        tuple,
        'lax',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        set,
        'lax',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'dict_keys',
        'lax',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        frozenset,
        'dict_values',
        'lax',
        'python',
        core_schemas=[core_schema.FrozenSetSchema],
    ),
    Row(
        isinstance,
        Any,
        'strict',
        'python',
        condition='`isinstance()` check returns True',
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        isinstance,
        '-',
        'strict',
        'JSON',
        condition='never valid',
        core_schemas=[core_schema.IsInstanceSchema],
    ),
    Row(
        callable,
        Any,
        'strict',
        'python',
        condition='`callable()` check returns True',
        core_schemas=[core_schema.CallableSchema],
    ),
    Row(
        callable,
        '-',
        'strict',
        'JSON',
        condition='never valid',
        core_schemas=[core_schema.CallableSchema],
    ),
]
