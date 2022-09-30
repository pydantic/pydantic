from __future__ import annotations as _annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum, IntEnum
from pathlib import Path, PurePath
from typing import Any, Callable
from uuid import UUID

from pydantic_core import PydanticValueError, core_schema

__all__ = ('SCHEMA_LOOKUP',)


def name_as_schema(t: type[Any]) -> core_schema.CoreSchema:
    return {'type': t.__name__}


def enum_schema(enum_type: type[Enum]) -> core_schema.CoreSchema:
    def to_enum(v: Any, **_kwargs: Any) -> Enum:
        try:
            return enum_type(v)
        except ValueError:
            raise PydanticValueError('enum', 'Input is not a valid enum member')

    literal_schema = core_schema.literal_schema(*[m.value for m in enum_type.__members__.values()])

    if issubclass(enum_type, IntEnum):
        return core_schema.chain_schema(
            core_schema.int_schema(), literal_schema, core_schema.function_plain_schema(to_enum)
        )
    elif issubclass(enum_type, str):
        return core_schema.chain_schema(
            core_schema.string_schema(), literal_schema, core_schema.function_plain_schema(to_enum)
        )
    else:
        return core_schema.function_after_schema(
            schema=literal_schema,
            function=to_enum,
        )


def decimal_validator(v: int | float | str, **_kwargs: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v

    v = str(v)

    try:
        return Decimal(v)
    except DecimalException:
        raise PydanticValueError('decimal_parsing', 'Input should be a valid decimal')


def decimal_schema(_decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
    return core_schema.function_after_schema(
        decimal_validator,
        core_schema.union_schema(
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.string_schema(strip_whitespace=True),
        ),
    )


def uuid_validator(input_value: str | bytes, **_kwargs: Any) -> UUID:
    try:
        if isinstance(input_value, str):
            return UUID(input_value)
        else:
            try:
                return UUID(input_value.decode())
            except ValueError:
                # 16 bytes in big-endian order as the bytes argument fail
                # the above check
                return UUID(bytes=input_value)
    except ValueError:
        raise PydanticValueError('uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID')


def uuid_schema(uuid_type: type[UUID]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    return core_schema.union_schema(
        core_schema.is_instance_schema(uuid_type),
        core_schema.function_after_schema(
            uuid_validator,
            core_schema.union_schema(
                core_schema.string_schema(),
                core_schema.bytes_schema(),
                custom_error_kind='uuid_type',
                custom_error_message='Input should be a valid UUID, string, or bytes',
            ),
        ),
        strict=True,
    )


def path_validator(v: str) -> Path:
    try:
        return Path(v)
    except TypeError:
        raise PydanticValueError('path', 'Input is not a valid path')


def path_schema(path_type: type[PurePath]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(...)` as above?
    return core_schema.union_schema(
        core_schema.is_instance_schema(path_type),
        core_schema.function_after_schema(
            path_validator,
            core_schema.string_schema(),
        ),
        strict=True,
    )


SCHEMA_LOOKUP: dict[type[Any], Callable[[type[Any]], core_schema.CoreSchema]] = {
    date: name_as_schema,
    datetime: name_as_schema,
    time: name_as_schema,
    timedelta: name_as_schema,
    Enum: enum_schema,
    Decimal: decimal_schema,
    UUID: uuid_schema,
    PurePath: path_schema,
}
