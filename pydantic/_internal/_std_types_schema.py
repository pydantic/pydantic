"""
Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.

We also deferr accessing attributes of the modules we import until runtime so that monkey patching works, e.g.
it is common to monkey patch datetime.datetime in tests (even we do that).
"""
from __future__ import annotations as _annotations

import collections
import collections.abc
import datetime
import decimal
import enum
import inspect
import ipaddress
import os
import pathlib
import typing
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from pydantic_core import CoreSchema, MultiHostUrl, PydanticCustomError, Url, core_schema
from typing_extensions import get_args, get_origin

from ..errors import PydanticInvalidForJsonSchema
from ..json_schema import JsonSchemaValue, update_json_schema
from . import _serializers, _validators
from ._core_metadata import build_metadata_dict
from ._core_utils import get_type_ref
from ._schema_generation_shared import GetCoreSchemaHandler, GetJsonSchemaHandler

if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema

    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]


class SchemaGeneratorBase:
    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return handler(source_type)

    def __get_pydantic_json_schema__(
        self, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(schema)


@dataclass
class SimpleSchemaGenerator(SchemaGeneratorBase):
    schema: core_schema.CoreSchema | None = None
    json_schema: JsonSchemaValue | None = None

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.schema or handler(source_type)

    def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return self.json_schema or handler(schema)

    def __hash__(self) -> int:
        return id(self)


@dataclass
class SubclassSchemaGenerator(SchemaGeneratorBase):
    core_schema: core_schema.CoreSchema

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            lambda x: x if isinstance(x, source_type) else source_type(x),
            self.core_schema,
        )

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.core_schema)

    def __hash__(self) -> int:
        return id(self)


def is_subclass(tp_or_origin: Any, types: tuple[Any, ...]) -> bool:
    try:
        if issubclass(tp_or_origin, types):
            return True
    except TypeError:
        # not a class, might be a GenericAlias e.g. from List[T]
        return False
    return False


def is_exact_class(tp_or_origin: Any, types: tuple[Any, ...]) -> bool:
    if tp_or_origin in types:
        return True
    return False


def get_schema_generator_for_known_type(tp: Any) -> SchemaGeneratorBase:  # noqa: C901
    origin: Any = get_origin(tp)
    pathlib_types: tuple[Any, ...] = (
        os.PathLike,
        pathlib.PurePath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
        pathlib.PosixPath,
        pathlib.WindowsPath,
        pathlib.Path,
    )
    deque_types: tuple[Any, ...] = (typing.Deque, collections.deque)
    ordered_dict_types: tuple[Any, ...] = (typing.OrderedDict, collections.OrderedDict)
    simple_generic_collection_types: tuple[Any, ...] = (typing.List, list, typing.Set, set, typing.FrozenSet, frozenset)

    for date_time_type, schema in [
        # order between datetime and date matters since the latter
        # is a subclass of the former
        (datetime.datetime, core_schema.datetime_schema()),
        (datetime.date, core_schema.date_schema()),
        (datetime.time, core_schema.time_schema()),
        (datetime.timedelta, core_schema.timedelta_schema()),
    ]:
        if is_subclass(tp, (date_time_type,)):
            if tp is date_time_type:
                return SimpleSchemaGenerator(schema)
            return SubclassSchemaGenerator(schema)

    # collections
    if is_subclass(tp, simple_generic_collection_types) or is_subclass(origin, simple_generic_collection_types):
        return SingleGenericCollectionSchema()
    elif is_subclass(tp, (enum.Enum,)):
        return EnumSchemaGenerator()
    elif tp is decimal.Decimal:
        return DecimalSchemaGenerator()
    elif is_subclass(tp, pathlib_types) or is_subclass(origin, pathlib_types) or origin is os.PathLike:
        return PathLikeSchemaGenerator()
    elif tp is uuid.UUID:
        return UUIDSchemaGenerator()
    elif is_subclass(tp, deque_types) or is_subclass(origin, deque_types):
        return DequeueSchemaGenerator()
    elif is_subclass(tp, ordered_dict_types) or is_subclass(origin, ordered_dict_types):
        return OrderedDictSchemaGenerator()
    elif tp is ipaddress.IPv4Address:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(_validators.ip_v4_address_validator),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv4Address),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv4'},
        )
    elif tp is ipaddress.IPv4Interface:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(
                    _validators.ip_v4_interface_validator,
                ),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv4Interface),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv4interface'},
        )
    elif tp is ipaddress.IPv4Network:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(_validators.ip_v4_network_validator),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv4Network),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv4network'},
        )
    elif tp is ipaddress.IPv6Address:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(_validators.ip_v6_address_validator),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv6Address),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv6'},
        )
    elif tp is ipaddress.IPv6Interface:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(_validators.ip_v6_interface_validator),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv6Interface),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv6interface'},
        )
    elif tp is ipaddress.IPv6Network:
        return SimpleSchemaGenerator(
            core_schema.lax_or_strict_schema(
                lax_schema=core_schema.general_plain_validator_function(_validators.ip_v6_network_validator),
                strict_schema=_make_strict_ip_schema(ipaddress.IPv6Network),
                serialization=core_schema.to_string_ser_schema(),
            ),
            {'type': 'string', 'format': 'ipv6network'},
        )
    elif tp is Url:
        return SimpleSchemaGenerator({'type': 'url'})
    elif tp is MultiHostUrl:
        return SimpleSchemaGenerator({'type': 'multi-host-url'})

    raise LookupError(f'{tp} is not a known type or marker')


def get_arg_from_generic(type_: Any, idx: int = 0) -> Any:
    """
    Get the argument from a typing object, e.g. `List[int]` -> `int`, or `Any` if no argument.
    """
    try:
        return get_args(type_)[idx]
    except IndexError:
        return Any


def invert_type_name_map(original_dict: dict[str, tuple[list[Any], Any]]) -> dict[Any, tuple[str, Any]]:
    result_dict: dict[Any, tuple[str, Any]] = {}
    for key, (types, type) in original_dict.items():
        for t in types:
            result_dict[t] = (key, type)
    return result_dict


def get_type_name(type_name_map: dict[str, tuple[list[Any], Any]], origin: Any) -> tuple[str, Any]:
    inverted = invert_type_name_map(type_name_map)
    for tp, (name, builtin_tp) in inverted.items():
        if issubclass(origin, tp):
            return name, builtin_tp
    raise Exception  # TODO


BUILTINS_TYPE_MAP: dict[Any, Any] = {
    typing.List: list,
    typing.Set: set,
    typing.FrozenSet: frozenset,
    list: list,
    set: set,
    frozenset: frozenset,
}


def builtin_type_from_annotation_type(tp: Any) -> Any | None:
    origin: Any = get_origin(tp) or tp
    return BUILTINS_TYPE_MAP.get(origin, None)


def parent_builtin_type_from_annotation_type(tp: Any) -> Any:
    origin: Any = get_origin(tp) or tp
    for k, v in BUILTINS_TYPE_MAP.items():
        if issubclass(origin, k):
            return v
    raise Exception  # TODO


class SingleGenericCollectionSchema(SchemaGeneratorBase):
    """
    Generate schemas for lists and sets
    """

    js_core_schema: core_schema.CoreSchema

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        origin: Any = get_origin(source_type) or source_type
        builtin_type = parent_builtin_type_from_annotation_type(origin)
        schema: core_schema.CoreSchema = {  # type: ignore[misc,assignment]
            'type': builtin_type.__name__,  # this is just a 'nice' coincidence
            'items_schema': handler.generate_schema(get_arg_from_generic(source_type, 0)),
        }

        self.js_core_schema = schema

        if builtin_type_from_annotation_type(origin) is builtin_type:
            return schema
        else:
            # Ensure the validated value is converted back to the specific subclass type
            # NOTE: we might have better performance by using a tuple or list validator for the schema here,
            # but if you care about performance, you can define your own schema.
            # We should optimize for compatibility, not performance in this case
            return core_schema.no_info_after_validator_function(
                lambda x: x if isinstance(x, origin) else origin(x), schema
            )

    def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.js_core_schema)


class EnumSchemaGenerator(SchemaGeneratorBase):
    cases: list[Any] = []
    json_schema_updates: dict[str, Any] = {}

    def __get_pydantic_core_schema__(self, enum_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        # we use this type instead of the type we had in get_schema_generator_for_known_type because
        # the type passed to get_schema_generator_for_known_type may have been a typevar bound
        # but this is always the concrete type
        self.enum_type = enum_type
        self.cases = cases = list(enum_type.__members__.values())
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        self.json_schema_updates.update({'title': enum_type.__name__, 'description': description})
        self.json_schema_updates = {k: v for k, v in self.json_schema_updates.items() if v is not None}

        if not cases:
            # Use an isinstance check for enums with no cases.
            # This won't work with serialization or JSON schema, but that's okay -- the most important
            # use case for this is creating typevar bounds for generics that should be restricted to enums.
            # This is more consistent than it might seem at first, since you can only subclass enum.Enum
            # (or subclasses of enum.Enum) if all parent classes have no cases.
            return core_schema.is_instance_schema(enum_type)

        if len(cases) == 1:
            expected = repr(cases[0].value)
        else:
            expected = ','.join([repr(case.value) for case in cases[:-1]]) + f' or {cases[-1].value!r}'

        def to_enum(__input_value: Any, info: core_schema.ValidationInfo | None = None) -> enum.Enum:
            try:
                return enum_type(__input_value)
            except ValueError:
                raise PydanticCustomError('enum', f'Input should be {expected}', {'expected': expected})

        enum_ref = get_type_ref(enum_type)
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == 'An enumeration.'
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None

        to_enum_validator = core_schema.general_plain_validator_function(to_enum)
        if issubclass(enum_type, int):
            # this handles `IntEnum`, and also `Foobar(int, Enum)`
            self.json_schema_updates['type'] = 'integer'
            lax = core_schema.chain_schema([core_schema.int_schema(), to_enum_validator])
            # Allow str from JSON to get better error messages (str will still fail validation in to_enum)
            # Disallow float from JSON due to strict mode
            strict = core_schema.is_instance_schema(enum_type, json_types={'int', 'str'}, json_function=to_enum)
        elif issubclass(enum_type, str):
            # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
            self.json_schema_updates['type'] = 'string'
            lax = core_schema.chain_schema([core_schema.str_schema(), to_enum_validator])
            # Allow all types from JSON to get better error messages
            # (numeric types will still fail validation in to_enum)
            strict = core_schema.is_instance_schema(
                enum_type, json_types={'int', 'str', 'float'}, json_function=to_enum
            )
        elif issubclass(enum_type, float):
            self.json_schema_updates['type'] = 'numeric'
            lax = core_schema.chain_schema([core_schema.float_schema(), to_enum_validator])
            # Allow str from JSON to get better error messages (str will still fail validation in to_enum)
            strict = core_schema.is_instance_schema(
                enum_type, json_types={'int', 'str', 'float'}, json_function=to_enum
            )
        else:
            lax = to_enum_validator
            strict = core_schema.is_instance_schema(
                enum_type, json_types={'float', 'int', 'str'}, json_function=to_enum
            )
        return core_schema.lax_or_strict_schema(
            lax_schema=lax,
            strict_schema=strict,
            ref=enum_ref,
        )

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        if not self.cases:
            # see note above about enums with no cases
            raise PydanticInvalidForJsonSchema(
                f'The enum {self.enum_type} cannot generate a JSON schema because it has no cases'
            )
        json_schema = handler(core_schema.literal_schema([x.value for x in self.cases]))
        original_schema = handler.resolve_ref_schema(json_schema)
        update_json_schema(original_schema, self.json_schema_updates)
        return json_schema


class DecimalSchemaGenerator(SchemaGeneratorBase):
    def __init__(self):
        self.decimal_validator = _validators.DecimalValidator()

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        metadata = build_metadata_dict(
            cs_update_function=self.decimal_validator.__pydantic_update_schema__,
        )
        lax = core_schema.general_after_validator_function(
            self.decimal_validator,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(decimal.Decimal, json_types={'int', 'float'}),
                    core_schema.int_schema(),
                    core_schema.float_schema(),
                    core_schema.str_schema(strip_whitespace=True),
                ],
                strict=True,
            ),
        )
        strict = core_schema.custom_error_schema(
            core_schema.general_after_validator_function(
                self.decimal_validator,
                core_schema.is_instance_schema(decimal.Decimal, json_types={'int', 'float'}),
            ),
            custom_error_type='decimal_type',
            custom_error_message='Input should be a valid Decimal instance or decimal string in JSON',
        )
        return core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict, metadata=metadata)

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.decimal_validator.json_schema_override_schema())


class UUIDSchemaGenerator(SchemaGeneratorBase):
    def __get_pydantic_json_schema__(self, _schema: CoreSchema, _handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'uuid'}

    def __get_pydantic_core_schema__(self, source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
        lax = core_schema.union_schema(
            [
                core_schema.is_instance_schema(source_type, json_types={'str'}),
                core_schema.general_after_validator_function(
                    _validators.uuid_validator,
                    core_schema.union_schema([core_schema.str_schema(), core_schema.bytes_schema()]),
                ),
            ],
            custom_error_type='uuid_type',
            custom_error_message='Input should be a valid UUID, string, or bytes',
            strict=True,
        )

        strict = core_schema.chain_schema(
            [
                core_schema.is_instance_schema(source_type, json_types={'str'}),
                core_schema.union_schema(
                    [
                        core_schema.is_instance_schema(uuid.UUID),
                        core_schema.chain_schema(
                            [
                                core_schema.str_schema(),
                                core_schema.general_plain_validator_function(_validators.uuid_validator),
                            ]
                        ),
                    ]
                ),
            ],
        )
        return core_schema.lax_or_strict_schema(
            lax_schema=lax,
            strict_schema=strict,
            serialization=core_schema.to_string_ser_schema(),
        )


class PathLikeSchemaGenerator(SchemaGeneratorBase):
    def __get_pydantic_core_schema__(self, source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        construct_path = pathlib.PurePath if source_type is os.PathLike else source_type
        metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'path'}])

        def path_validator(__input_value: str) -> os.PathLike[Any]:
            try:
                return construct_path(__input_value)  # type: ignore
            except TypeError as e:
                raise PydanticCustomError('path_type', 'Input is not a valid path') from e

        instance_schema = core_schema.is_instance_schema(source_type, json_types={'str'}, json_function=path_validator)

        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.union_schema(
                [
                    instance_schema,
                    core_schema.no_info_after_validator_function(path_validator, core_schema.str_schema()),
                ],
                custom_error_type='path_type',
                custom_error_message='Input is not a valid path',
                strict=True,
            ),
            strict_schema=instance_schema,
            serialization=core_schema.to_string_ser_schema(),
            metadata=metadata,
        )

    def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'path'}


def _deque_ser_schema(
    inner_schema: core_schema.CoreSchema | None = None,
) -> core_schema.WrapSerializerFunctionSerSchema:
    return core_schema.wrap_serializer_function_ser_schema(
        _serializers.serialize_deque, info_arg=True, schema=inner_schema or core_schema.any_schema()
    )


def _deque_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_wrap_validator_function(
            _validators.deque_any_validator,
            core_schema.list_schema(),
        ),
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: x if isinstance(x, collections.deque) else collections.deque(x),
            core_schema.is_instance_schema(collections.deque, json_types={'list'}),
        ),
        serialization=_deque_ser_schema(),
    )


class DequeueSchemaGenerator(SchemaGeneratorBase):
    inner_schema: core_schema.CoreSchema = core_schema.any_schema()

    def __get_pydantic_core_schema__(self, obj: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if obj == collections.deque:
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
            self.inner_schema = inner_schema = handler.generate_schema(arg)
            # Use a lambda here so `apply_metadata` is called on the decimal_validator before the override is generated
            lax_schema = core_schema.general_wrap_validator_function(
                _validators.deque_typed_validator,
                core_schema.list_schema(inner_schema, strict=False),
            )
        return core_schema.lax_or_strict_schema(
            lax_schema=lax_schema,
            strict_schema=core_schema.chain_schema(
                [core_schema.is_instance_schema(collections.deque, json_types={'list'}), lax_schema],
            ),
            serialization=_deque_ser_schema(inner_schema),
        )

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(core_schema.list_schema(self.inner_schema))


def _ordered_dict_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.general_wrap_validator_function(
            _validators.ordered_dict_any_validator, core_schema.dict_schema()
        ),
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: collections.OrderedDict(x),
            core_schema.is_instance_schema(collections.OrderedDict, json_types={'dict'}),
        ),
    )


class OrderedDictSchemaGenerator(SchemaGeneratorBase):
    inner_schema: core_schema.CoreSchema = core_schema.any_schema()

    def __get_pydantic_core_schema__(self, obj: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        try:
            keys_arg, values_arg = get_args(obj)
        except ValueError:
            # not argument bare `OrderedDict` is equivalent to `OrderedDict[Any, Any]`
            return _ordered_dict_any_schema()

        if keys_arg == typing.Any and values_arg == typing.Any:
            # `OrderedDict[Any, Any]`
            return _ordered_dict_any_schema()
        else:
            self.inner_schema = inner_schema = core_schema.dict_schema(handler.generate_schema(keys_arg), handler.generate_schema(values_arg))
            return core_schema.lax_or_strict_schema(
                lax_schema=core_schema.no_info_after_validator_function(
                    collections.OrderedDict,
                    inner_schema,
                ),
                strict_schema=core_schema.no_info_after_validator_function(
                    collections.OrderedDict,
                    core_schema.chain_schema(
                        [
                            core_schema.is_instance_schema(collections.OrderedDict, json_types={'dict'}),
                            inner_schema,
                        ],
                    ),
                ),
            )

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(core_schema.list_schema(self.inner_schema))


def _make_strict_ip_schema(tp: type[Any]) -> CoreSchema:
    return core_schema.general_after_validator_function(
        lambda x, _: tp(x),
        core_schema.is_instance_schema(tp, json_types={'str'}),
    )
