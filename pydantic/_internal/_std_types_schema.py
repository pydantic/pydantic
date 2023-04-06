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

from pydantic_core import CoreSchema, MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import Literal, get_args

from ..json_schema import update_json_schema
from . import _serializers, _validators
from ._core_metadata import build_metadata_dict
from ._core_utils import get_type_ref

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

    enum_ref = get_type_ref(enum_type)
    literal_schema = core_schema.literal_schema(
        [m.value for m in enum_type.__members__.values()],
    )
    description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
    if description == 'An enumeration.':  # This is the default value provided by enum.EnumMeta.__new__; don't use it
        description = None
    updates = {'title': enum_type.__name__, 'description': description}
    updates = {k: v for k, v in updates.items() if v is not None}
    metadata = build_metadata_dict(
        js_cs_override=literal_schema.copy(), js_modify_function=lambda s: update_json_schema(s, updates)
    )

    lax: CoreSchema
    json_type: Literal['int', 'float', 'str']
    if issubclass(enum_type, int):
        # this handles `IntEnum`, and also `Foobar(int, Enum)`
        updates['type'] = 'integer'
        lax = core_schema.chain_schema(
            [core_schema.int_schema(), literal_schema, core_schema.general_plain_validator_function(to_enum)],
            metadata=metadata,
        )
        json_type = 'int'
    elif issubclass(enum_type, str):
        # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
        updates['type'] = 'string'
        lax = core_schema.chain_schema(
            [core_schema.str_schema(), literal_schema, core_schema.general_plain_validator_function(to_enum)],
            metadata=metadata,
        )
        json_type = 'str'
    else:
        lax = core_schema.general_after_validator_function(to_enum, literal_schema, metadata=metadata)
        json_type = 'str'
    return core_schema.lax_or_strict_schema(
        lax_schema=lax,
        strict_schema=core_schema.is_instance_schema(enum_type, json_types={json_type}),
        ref=enum_ref,
        metadata=metadata,
    )


@schema_function(Decimal)
def decimal_schema(_schema_generator: GenerateSchema, _decimal_type: type[Decimal]) -> core_schema.LaxOrStrictSchema:
    decimal_validator = _validators.DecimalValidator()
    metadata = build_metadata_dict(
        cs_update_function=decimal_validator.__pydantic_update_schema__,
        # Use a lambda here so `apply_metadata` is called on the decimal_validator before the override is generated
        js_cs_override=lambda: decimal_validator.json_schema_override_schema(),
    )
    lax = core_schema.general_after_validator_function(
        decimal_validator,
        core_schema.union_schema(
            [
                core_schema.is_instance_schema(Decimal, json_types={'int', 'float'}),
                core_schema.int_schema(),
                core_schema.float_schema(),
                core_schema.str_schema(strip_whitespace=True),
            ],
            strict=True,
        ),
    )
    strict = core_schema.custom_error_schema(
        core_schema.general_after_validator_function(
            decimal_validator,
            core_schema.is_instance_schema(Decimal, json_types={'int', 'float'}),
        ),
        custom_error_type='decimal_type',
        custom_error_message='Input should be a valid Decimal instance or decimal string in JSON',
    )
    return core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict, metadata=metadata)


@schema_function(UUID)
def uuid_schema(_schema_generator: GenerateSchema, uuid_type: type[UUID]) -> core_schema.LaxOrStrictSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'uuid'})
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    lax = core_schema.union_schema(
        [
            core_schema.is_instance_schema(uuid_type, json_types={'str'}),
            core_schema.general_after_validator_function(
                _validators.uuid_validator,
                core_schema.union_schema([core_schema.str_schema(), core_schema.bytes_schema()]),
            ),
        ],
        custom_error_type='uuid_type',
        custom_error_message='Input should be a valid UUID, string, or bytes',
        strict=True,
        metadata=metadata,
    )

    return core_schema.lax_or_strict_schema(
        lax_schema=lax,
        strict_schema=core_schema.chain_schema(
            [
                core_schema.is_instance_schema(uuid_type, json_types={'str'}),
                core_schema.union_schema(
                    [
                        core_schema.is_instance_schema(UUID),
                        core_schema.chain_schema(
                            [
                                core_schema.str_schema(),
                                core_schema.general_plain_validator_function(_validators.uuid_validator),
                            ]
                        ),
                    ]
                ),
            ],
            metadata=metadata,
        ),
    )


@schema_function(PurePath)
def path_schema(_schema_generator: GenerateSchema, path_type: type[PurePath]) -> core_schema.LaxOrStrictSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'path'})
    # TODO, is this actually faster than `function_after(...)` as above?
    lax = core_schema.union_schema(
        [
            core_schema.is_instance_schema(path_type, json_types={'str'}, metadata=metadata),
            core_schema.general_after_validator_function(
                _validators.path_validator,
                core_schema.str_schema(),
                metadata=metadata,
            ),
        ],
        custom_error_type='path_type',
        custom_error_message='Input is not a valid path',
        strict=True,
    )

    return core_schema.lax_or_strict_schema(
        lax_schema=lax,
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: path_type(x),
            core_schema.is_instance_schema(path_type, json_types={'str'}),
            serialization=core_schema.to_string_ser_schema(),
            metadata=metadata,
        ),
    )


def _deque_ser_schema(
    inner_schema: core_schema.CoreSchema | None = None,
) -> core_schema.WrapSerializerFunctionSerSchema:
    return core_schema.general_wrap_serializer_function_ser_schema(
        _serializers.serialize_deque, schema=inner_schema or core_schema.any_schema()
    )


def _deque_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_wrap_validator_function(
            _validators.deque_any_validator,
            core_schema.list_schema(),
        ),
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: deque(x),
            core_schema.is_instance_schema(deque, json_types={'list'}),
        ),
        serialization=_deque_ser_schema(),
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
        # Use a lambda here so `apply_metadata` is called on the decimal_validator before the override is generated
        metadata = build_metadata_dict(js_cs_override=lambda: core_schema.list_schema(inner_schema))
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.general_after_validator_function(
                _validators.deque_typed_validator,
                core_schema.list_schema(inner_schema),
                serialization=_deque_ser_schema(inner_schema),
                metadata=metadata,
            ),
            strict_schema=core_schema.chain_schema(
                [
                    core_schema.is_instance_schema(deque, json_types={'list'}),
                    core_schema.list_schema(inner_schema, allow_any_iter=True),
                    core_schema.general_plain_validator_function(
                        _validators.deque_typed_validator,
                    ),
                ],
                metadata=metadata,
            ),
            serialization=_deque_ser_schema(inner_schema),
        )


def _ordered_dict_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_wrap_validator_function(
            _validators.ordered_dict_any_validator, core_schema.dict_schema()
        ),
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: OrderedDict(x),
            core_schema.is_instance_schema(OrderedDict, json_types={'dict'}),
        ),
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
        inner_schema = core_schema.dict_schema(
            schema_generator.generate_schema(keys_arg), schema_generator.generate_schema(values_arg)
        )
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.general_after_validator_function(
                _validators.ordered_dict_typed_validator,
                core_schema.dict_schema(
                    schema_generator.generate_schema(keys_arg), schema_generator.generate_schema(values_arg)
                ),
            ),
            strict_schema=core_schema.general_after_validator_function(
                lambda x, _: OrderedDict(x),
                core_schema.chain_schema(
                    [
                        core_schema.is_instance_schema(OrderedDict, json_types={'dict'}),
                        core_schema.dict_schema(inner_schema),
                    ],
                ),
            ),
        )


def make_strict_ip_schema(tp: type[Any], metadata: Any) -> CoreSchema:
    return core_schema.general_after_validator_function(
        lambda x, _: tp(x),
        core_schema.is_instance_schema(tp, json_types={'str'}),
        metadata=metadata,
    )


@schema_function(IPv4Address)
def ip_v4_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv4'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(_validators.ip_v4_address_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv4Address, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv4Interface)
def ip_v4_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv4interface'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(
            _validators.ip_v4_interface_validator, metadata=metadata
        ),
        strict_schema=make_strict_ip_schema(IPv4Interface, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv4Network)
def ip_v4_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv4network'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(_validators.ip_v4_network_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv4Network, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Address)
def ip_v6_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv6'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(_validators.ip_v6_address_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv6Address, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Interface)
def ip_v6_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv6interface'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(
            _validators.ip_v6_interface_validator, metadata=metadata
        ),
        strict_schema=make_strict_ip_schema(IPv6Interface, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Network)
def ip_v6_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_override={'type': 'string', 'format': 'ipv6network'})
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_plain_validator_function(_validators.ip_v6_network_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv6Network, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(Url)
def url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    return {'type': 'url'}


@schema_function(MultiHostUrl)
def multi_host_url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    return {'type': 'multi-host-url'}
