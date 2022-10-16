from __future__ import annotations as _annotations

import typing
from collections import deque, OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import PurePath
from typing import Any, Callable
from uuid import UUID

from pydantic_core import PydanticCustomError, core_schema
from typing_extensions import get_args

from . import _validators

__all__ = ('SCHEMA_LOOKUP',)


def name_as_schema(t: type[Any]) -> core_schema.CoreSchema:
    return {'type': t.__name__}


def enum_schema(enum_type: type[Enum]) -> core_schema.CoreSchema:
    def to_enum(v: Any, **_kwargs: Any) -> Enum:
        try:
            return enum_type(v)
        except ValueError:
            raise PydanticCustomError('enum', 'Input is not a valid enum member')

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
            literal_schema,
            to_enum,
        )


def decimal_schema(_decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
    decimal_validator = _validators.DecimalValidator()
    return core_schema.function_after_schema(
        core_schema.union_schema(
            core_schema.is_instance_schema(Decimal, json_types={'int', 'float'}),
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.string_schema(strip_whitespace=True),
            strict=True,
        ),
        decimal_validator,
        extra=decimal_validator,
    )


def uuid_schema(uuid_type: type[UUID]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    return core_schema.union_schema(
        core_schema.is_instance_schema(uuid_type),
        core_schema.function_after_schema(
            core_schema.union_schema(
                core_schema.string_schema(),
                core_schema.bytes_schema(),
            ),
            _validators.uuid_validator,
        ),
        custom_error_kind='uuid_type',
        custom_error_message='Input should be a valid UUID, string, or bytes',
        strict=True,
    )


def path_schema(path_type: type[PurePath]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(...)` as above?
    return core_schema.union_schema(
        core_schema.is_instance_schema(path_type),
        core_schema.function_after_schema(
            core_schema.string_schema(),
            _validators.path_validator,
        ),
        custom_error_kind='path_type',
        custom_error_message='Input is not a valid path',
        strict=True,
    )


def _deque_any_schema() -> core_schema.FunctionWrapSchema:
    return core_schema.function_wrap_schema(_validators.deque_any_validator, core_schema.list_schema())


def deque_schema(obj: Any) -> core_schema.CoreSchema:
    if obj == deque:
        # bare `deque` type used as annotation
        return _deque_any_schema()

    try:
        arg = get_args(obj)[0]
    except IndexError:
        # not argument bare `Deque` is equivalent to `Deque[Any]`
        return _deque_any_schema()

    if arg == typing.Any:
        # `Deque[Any]`
        return _deque_any_schema()
    else:
        # `Deque[Something]`
        from ._babelfish import generate_schema

        return core_schema.function_after_schema(
            core_schema.list_schema(generate_schema(arg)),
            _validators.deque_typed_validator,
        )


def _ordered_dict_any_schema() -> core_schema.FunctionWrapSchema:
    return core_schema.function_wrap_schema(_validators.ordered_dict_any_validator, core_schema.dict_schema())


def ordered_dict_schema(obj: Any):
    if obj == OrderedDict:
        # bare `ordered_dict` type used as annotation
        return _ordered_dict_any_schema()

    try:
        keys_arg, values_arg = get_args(obj)
    except ValueError:
        # not argument bare `OrderedDict` is equivalent to `OrderedDict[Any, Any]`
        return _ordered_dict_any_schema()

    if keys_arg == typing.Any and values_arg == typing.Any:
        # `OrderedDict[Any, Any]`
        return _ordered_dict_any_schema()
    else:
        # `OrderedDict[Foo, Bar]`
        from ._babelfish import generate_schema

        return core_schema.function_after_schema(
            core_schema.dict_schema(generate_schema(keys_arg), generate_schema(values_arg)),
            _validators.ordered_dict_typed_validator,
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
    deque: deque_schema,
    OrderedDict: ordered_dict_schema,
}
