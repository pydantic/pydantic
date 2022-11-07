"""
Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""
from __future__ import annotations as _annotations

import typing
from collections import OrderedDict, deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import PurePath
from typing import Any, Callable
from uuid import UUID

from pydantic_core import MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import get_args

from . import _validators

if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema

    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]

__all__ = ('SCHEMA_LOOKUP',)

SCHEMA_LOOKUP: dict[type[Any], StdSchemaFunction] = {}


def schema_function(type: type[Any]) -> Callable[[StdSchemaFunction], StdSchemaFunction]:
    def wrapper(func: StdSchemaFunction) -> StdSchemaFunction:
        SCHEMA_LOOKUP[type] = func
        return func

    return wrapper


@schema_function(date)
@schema_function(datetime)
@schema_function(time)
@schema_function(timedelta)
def name_as_schema(_schema_generator: GenerateSchema, t: type[Any]) -> core_schema.CoreSchema:
    return {'type': t.__name__}  # type: ignore[return-value,misc]


@schema_function(Enum)
def enum_schema(_schema_generator: GenerateSchema, enum_type: type[Enum]) -> core_schema.CoreSchema:
    def to_enum(__input_value: Any, **_kwargs: Any) -> Enum:
        try:
            return enum_type(__input_value)
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


@schema_function(Decimal)
def decimal_schema(_schema_generator: GenerateSchema, _decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
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


@schema_function(UUID)
def uuid_schema(_schema_generator: GenerateSchema, uuid_type: type[UUID]) -> core_schema.UnionSchema:
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
        custom_error_type='uuid_type',
        custom_error_message='Input should be a valid UUID, string, or bytes',
        strict=True,
    )


@schema_function(PurePath)
def path_schema(_schema_generator: GenerateSchema, path_type: type[PurePath]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(...)` as above?
    return core_schema.union_schema(
        core_schema.is_instance_schema(path_type),
        core_schema.function_after_schema(
            core_schema.string_schema(),
            _validators.path_validator,
        ),
        custom_error_type='path_type',
        custom_error_message='Input is not a valid path',
        strict=True,
    )


def _deque_any_schema() -> core_schema.FunctionWrapSchema:
    return core_schema.function_wrap_schema(_validators.deque_any_validator, core_schema.list_schema())


@schema_function(deque)
def deque_schema(schema_generator: GenerateSchema, obj: Any) -> core_schema.CoreSchema:
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
        return core_schema.function_after_schema(
            core_schema.list_schema(schema_generator.generate_schema(arg)),
            _validators.deque_typed_validator,
        )


def _ordered_dict_any_schema() -> core_schema.FunctionWrapSchema:
    return core_schema.function_wrap_schema(_validators.ordered_dict_any_validator, core_schema.dict_schema())


@schema_function(OrderedDict)
def ordered_dict_schema(schema_generator: GenerateSchema, obj: Any) -> core_schema.CoreSchema:
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
        return core_schema.function_after_schema(
            core_schema.dict_schema(
                schema_generator.generate_schema(keys_arg), schema_generator.generate_schema(values_arg)
            ),
            _validators.ordered_dict_typed_validator,
        )


@schema_function(IPv4Address)
def ip_v4_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v4_address_validator)


@schema_function(IPv4Interface)
def ip_v4_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v4_interface_validator)


@schema_function(IPv4Network)
def ip_v4_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v4_network_validator)


@schema_function(IPv6Address)
def ip_v6_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v6_address_validator)


@schema_function(IPv6Interface)
def ip_v6_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v6_interface_validator)


@schema_function(IPv6Network)
def ip_v6_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.FunctionPlainSchema:
    return core_schema.function_plain_schema(_validators.ip_v6_network_validator)


@schema_function(Url)
def url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.UrlSchema:
    return {'type': 'url'}


@schema_function(MultiHostUrl)
def multi_host_url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.MultiHostUrlSchema:
    return {'type': 'multi-host-url'}
