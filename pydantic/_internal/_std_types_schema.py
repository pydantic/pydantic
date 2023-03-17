"""
Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""
from __future__ import annotations as _annotations

import inspect
import typing
from collections import OrderedDict, deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import PurePath
from typing import Any, Callable
from uuid import UUID

from pydantic_core import MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import get_args

from ..json_schema import JsonSchemaMetadata
from . import _serializers, _validators
from ._core_metadata import build_metadata_dict

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
def date_schema(_schema_generator: GenerateSchema, _t: type[Any]) -> core_schema.DateSchema:
    return core_schema.DateSchema(type='date')


@schema_function(datetime)
def datetime_schema(_schema_generator: GenerateSchema, _t: type[Any]) -> core_schema.DatetimeSchema:
    return core_schema.DatetimeSchema(type='datetime')


@schema_function(time)
def time_schema(_schema_generator: GenerateSchema, _t: type[Any]) -> core_schema.TimeSchema:
    return core_schema.TimeSchema(type='time')


@schema_function(timedelta)
def timedelta_schema(_schema_generator: GenerateSchema, _t: type[Any]) -> core_schema.TimedeltaSchema:
    return core_schema.TimedeltaSchema(type='timedelta')


@schema_function(Enum)
def enum_schema(_schema_generator: GenerateSchema, enum_type: type[Enum]) -> core_schema.CoreSchema:
    def to_enum(__input_value: Any, _: core_schema.ValidationInfo) -> Enum:
        try:
            return enum_type(__input_value)
        except ValueError:
            raise PydanticCustomError('enum', 'Input is not a valid enum member')

    enum_ref = f'{getattr(enum_type, "__module__", None)}.{enum_type.__qualname__}:{id(enum_type)}'
    literal_schema = core_schema.literal_schema(
        *[m.value for m in enum_type.__members__.values()],
        ref=enum_ref,
    )
    js_metadata = JsonSchemaMetadata(
        core_schema_override=literal_schema.copy(),
        source_class=enum_type,
        title=enum_type.__name__,
        description=inspect.cleandoc(enum_type.__doc__ or 'An enumeration.'),
    )
    metadata = build_metadata_dict(js_metadata=js_metadata)

    if issubclass(enum_type, int):
        # this handles `IntEnum`, and also `Foobar(int, Enum)`
        js_metadata['extra_updates'] = {'type': 'integer'}
        return core_schema.chain_schema(
            core_schema.int_schema(),
            literal_schema,
            core_schema.general_plain_validation_function(to_enum),
            metadata=metadata,
        )
    elif issubclass(enum_type, str):
        # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
        # TODO: add test for StrEnum in 3.11, and also for enums that inherit from str/int
        js_metadata['extra_updates'] = {'type': 'string'}
        return core_schema.chain_schema(
            core_schema.str_schema(),
            literal_schema,
            core_schema.general_plain_validation_function(to_enum),
            metadata=metadata,
        )
    else:
        return core_schema.general_after_validation_function(to_enum, literal_schema, metadata=metadata)


@schema_function(Decimal)
def decimal_schema(_schema_generator: GenerateSchema, _decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
    decimal_validator = _validators.DecimalValidator()
    metadata = build_metadata_dict(
        update_cs_function=decimal_validator.__pydantic_update_schema__,
        js_metadata=JsonSchemaMetadata(
            # Use a lambda here so `apply_metadata` is called on the decimal_validator before the override is generated
            core_schema_override=lambda: decimal_validator.json_schema_override_schema()
        ),
    )
    return core_schema.general_after_validation_function(
        decimal_validator,
        core_schema.union_schema(
            core_schema.is_instance_schema(Decimal, json_types={'int', 'float'}),
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.str_schema(strip_whitespace=True),
            strict=True,
        ),
        metadata=metadata,
    )


@schema_function(UUID)
def uuid_schema(_schema_generator: GenerateSchema, uuid_type: type[UUID]) -> core_schema.UnionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(
            source_class=UUID, type='string', format='uuid', modify_js_function=lambda schema: schema.pop('anyOf', None)
        )
    )
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    return core_schema.union_schema(
        core_schema.is_instance_schema(uuid_type),
        core_schema.general_after_validation_function(
            _validators.uuid_validator,
            core_schema.union_schema(
                core_schema.str_schema(),
                core_schema.bytes_schema(),
            ),
            metadata=metadata,
        ),
        custom_error_type='uuid_type',
        custom_error_message='Input should be a valid UUID, string, or bytes',
        strict=True,
    )


@schema_function(PurePath)
def path_schema(_schema_generator: GenerateSchema, path_type: type[PurePath]) -> core_schema.UnionSchema:
    metadata = build_metadata_dict(js_metadata=JsonSchemaMetadata(source_class=PurePath, type='string', format='path'))
    # TODO, is this actually faster than `function_after(...)` as above?
    return core_schema.union_schema(
        core_schema.is_instance_schema(path_type),
        core_schema.general_after_validation_function(
            _validators.path_validator,
            core_schema.str_schema(),
            metadata=metadata,
        ),
        custom_error_type='path_type',
        custom_error_message='Input is not a valid path',
        strict=True,
    )


def _deque_ser_schema(inner_schema: core_schema.CoreSchema | None = None) -> core_schema.FunctionWrapSerSchema:
    return core_schema.function_wrap_ser_schema(_serializers.serialize_deque, inner_schema or core_schema.any_schema())


def _deque_any_schema() -> core_schema.WrapFunctionSchema:
    return core_schema.general_wrap_validation_function(
        _validators.deque_any_validator, core_schema.list_schema(allow_any_iter=True), serialization=_deque_ser_schema()
    )


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
        inner_schema = schema_generator.generate_schema(arg)
        return core_schema.general_after_validation_function(
            _validators.deque_typed_validator,
            core_schema.list_schema(inner_schema),
            serialization=_deque_ser_schema(inner_schema),
        )


def _ordered_dict_any_schema() -> core_schema.WrapFunctionSchema:
    return core_schema.general_wrap_validation_function(
        _validators.ordered_dict_any_validator, core_schema.dict_schema()
    )


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
        return core_schema.general_after_validation_function(
            _validators.ordered_dict_typed_validator,
            core_schema.dict_schema(
                schema_generator.generate_schema(keys_arg), schema_generator.generate_schema(values_arg)
            ),
        )


@schema_function(IPv4Address)
def ip_v4_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv4Address, type='string', format='ipv4')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v4_address_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(IPv4Interface)
def ip_v4_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv4Interface, type='string', format='ipv4interface')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v4_interface_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(IPv4Network)
def ip_v4_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv4Network, type='string', format='ipv4network')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v4_network_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(IPv6Address)
def ip_v6_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv6Address, type='string', format='ipv6')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v6_address_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(IPv6Interface)
def ip_v6_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv6Interface, type='string', format='ipv6interface')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v6_interface_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(IPv6Network)
def ip_v6_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.PlainFunctionSchema:
    metadata = build_metadata_dict(
        js_metadata=JsonSchemaMetadata(source_class=IPv6Network, type='string', format='ipv6network')
    )
    return core_schema.general_plain_validation_function(
        _validators.ip_v6_network_validator, serialization=core_schema.to_string_ser_schema(), metadata=metadata
    )


@schema_function(Url)
def url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.UrlSchema:
    return {'type': 'url'}


@schema_function(MultiHostUrl)
def multi_host_url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.MultiHostUrlSchema:
    return {'type': 'multi-host-url'}
