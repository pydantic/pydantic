from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from pydantic_core import CoreSchema, core_schema


@dataclass
class Row:
    field_type: type[Any]
    input_type: type[Any]
    mode: Literal['lax', 'strict', 'both']
    input_format: Literal['python', 'JSON', 'python, JSON']
    condition: str | None = None
    valid_examples: list[Any] | None = None
    invalid_examples: list[Any] | None = None
    core_schema: type[CoreSchema] = None


table_infos: list[Row] = [
    Row(
        str,
        str,
        'both',
        'python, JSON',
        core_schema=core_schema.StringSchema,
    ),
    Row(
        str,
        bytes,
        'lax',
        'python',
        condition='assumes UTF-8, error on unicode decoding error',
        valid_examples=[b's'],
        invalid_examples=[b'\x81'],
        core_schema=core_schema.StringSchema,
    ),
    Row(
        str,
        bytearray,
        'lax',
        'python',
        condition='assumes UTF-8, error on unicode decoding error',
        valid_examples=[bytearray(b's' * 5)],
        invalid_examples=[bytearray(b'\x81' * 5)],
        core_schema=core_schema.StringSchema,
    ),
    Row(
        bytes,
        bytes,
        'both',
        'python',
        core_schema=core_schema.BytesSchema,
    ),
    Row(
        bytes,
        str,
        'lax',
        'python, JSON',
        valid_examples=['foo'],
        core_schema=core_schema.BytesSchema,
    ),
    Row(
        bytes,
        bytearray,
        'lax',
        'python',
        valid_examples=[bytearray(b's' * 5)],
        core_schema=core_schema.BytesSchema,
    ),
    Row(
        int,
        int,
        'both',
        'python, JSON',
        condition='max abs value 2^64 - i64 is used internally',
        core_schema=core_schema.IntSchema,
    ),
    Row(
        int,
        float,
        'lax',
        'python, JSON',
        condition='`i64`, must be exact int, e.g. `val % 1 == 0`, `nan`, `inf` raise errors',
        valid_examples=[2.0],
        invalid_examples=[2.1, 2.2250738585072011e308, float('nan'), float('inf')],
        core_schema=core_schema.IntSchema,
    ),
    Row(
        int,
        Decimal,
        'lax',
        'python, JSON',
        condition='`i64`, must be exact int, e.g. `val % 1 == 0`',
        valid_examples=[Decimal(2.0)],
        invalid_examples=[Decimal(2.1)],
        core_schema=core_schema.IntSchema,
    ),
    Row(
        int,
        bool,
        'lax',
        'python, JSON',
        valid_examples=[True, False],
        core_schema=core_schema.IntSchema,
    ),
    Row(
        int,
        str,
        'lax',
        'python, JSON',
        condition='`i64`, must be numeric only, e.g. `[0-9]+`',
        valid_examples=['123'],
        invalid_examples=['test'],
        core_schema=core_schema.IntSchema,
    ),
]
