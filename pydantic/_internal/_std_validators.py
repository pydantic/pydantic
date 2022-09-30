from __future__ import annotations as _annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable
from uuid import UUID
from pathlib import Path

from pydantic_core import schema_types as core_schema, PydanticValueError

__all__ = ('SCHEMA_LOOKUP',)


def name_as_schema(t: type[Any]) -> core_schema.Schema:
    return {'type': t.__name__}


def enum_schema(enum_type: type[Enum]) -> core_schema.FunctionSchema:
    return core_schema.FunctionSchema(
        type='function',
        mode='after',
        schema=core_schema.LiteralSchema(type='literal', expected=[m.value for m in enum_type.__members__.values()]),
        function=lambda x, **kwargs: enum_type(x),
    )


def decimal_schema(decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
    return core_schema.FunctionSchema(
        type='function',
        mode='after',
        schema=core_schema.UnionSchema(
            type='union',
            choices=[
                core_schema.IntSchema(type='int'),
                core_schema.FloatSchema(type='float'),
                core_schema.StringSchema(type='str'),
            ]
        ),
        function=lambda x, **kwargs: decimal_type(x),
    )


def uuid_validator(input: str | bytes | UUID, **_kwargs: Any) -> UUID:
    if isinstance(input, UUID):
        return input
    try:
        if isinstance(input, str):
            return UUID(input)
        else:
            try:
                return UUID(input.decode())
            except ValueError:
                # 16 bytes in big-endian order as the bytes argument fail
                # the above check
                return UUID(bytes=input)
    except ValueError:
        raise PydanticValueError('uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID')


def uuid_schema(_uuid_type: type[UUID]) -> core_schema.FunctionSchema:
    return core_schema.FunctionSchema(
        type='function',
        mode='after',
        schema=core_schema.UnionSchema(
            type='union',
            choices=[
                core_schema.StringSchema(type='str'),
                core_schema.BytesSchema(type='bytes'),
                core_schema.IsInstanceSchema(type='is-instance', class_=UUID),
            ]
        ),
        function=uuid_validator,
    )


SCHEMA_LOOKUP: dict[type[Any], Callable[[type[Any]], core_schema.Schema]] = {
    date: name_as_schema,
    datetime: name_as_schema,
    time: name_as_schema,
    timedelta: name_as_schema,
    Enum: enum_schema,
    Decimal: decimal_schema,
    UUID: uuid_schema,
}
