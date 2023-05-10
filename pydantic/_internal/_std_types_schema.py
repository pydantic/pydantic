"""
Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""
from __future__ import annotations as _annotations

import collections
import decimal
import inspect
import os
import typing
from collections import OrderedDict
from enum import Enum
from functools import partial
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, Callable, Iterable

from pydantic_core import (
    CoreSchema,
    MultiHostUrl,
    PydanticCustomError,
    PydanticKnownError,
    PydanticOmit,
    Url,
    core_schema,
)
from typing_extensions import get_args, get_origin

from ..json_schema import JsonSchemaValue, update_json_schema
from . import _known_annotated_metadata, _validators
from ._core_metadata import build_metadata_dict
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_dataclass
from ._schema_generation_shared import GetCoreSchemaHandler, GetJsonSchemaHandler

if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema

    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]


SCHEMA_LOOKUP: dict[type[Any], StdSchemaFunction] = {}


def schema_function(type: type[Any]) -> Callable[[StdSchemaFunction], StdSchemaFunction]:
    def wrapper(func: StdSchemaFunction) -> StdSchemaFunction:
        SCHEMA_LOOKUP[type] = func
        return func

    return wrapper


@schema_function(Enum)
def enum_schema(_schema_generator: GenerateSchema, enum_type: type[Enum]) -> core_schema.CoreSchema:
    cases = list(enum_type.__members__.values())

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

    def to_enum(__input_value: Any) -> Enum:
        try:
            return enum_type(__input_value)
        except ValueError:
            # The type: ignore on the next line is to ignore the requirement of LiteralString
            raise PydanticCustomError('enum', f'Input should be {expected}', {'expected': expected})  # type: ignore

    enum_ref = get_type_ref(enum_type)
    description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
    if description == 'An enumeration.':  # This is the default value provided by enum.EnumMeta.__new__; don't use it
        description = None
    updates = {'title': enum_type.__name__, 'description': description}
    updates = {k: v for k, v in updates.items() if v is not None}

    def update_schema(_, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        json_schema = handler(core_schema.literal_schema([x.value for x in cases]))
        original_schema = handler.resolve_ref_schema(json_schema)
        update_json_schema(original_schema, updates)
        return json_schema

    metadata = build_metadata_dict(js_functions=[update_schema])

    to_enum_validator = core_schema.no_info_plain_validator_function(to_enum)
    if issubclass(enum_type, int):
        # this handles `IntEnum`, and also `Foobar(int, Enum)`
        updates['type'] = 'integer'
        lax = core_schema.chain_schema([core_schema.int_schema(), to_enum_validator])
        # Disallow float from JSON due to strict mode
        strict = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(to_enum, core_schema.int_schema()),
            python_schema=core_schema.is_instance_schema(enum_type),
        )
    elif issubclass(enum_type, str):
        # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
        updates['type'] = 'string'
        lax = core_schema.chain_schema([core_schema.str_schema(), to_enum_validator])
        strict = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(to_enum, core_schema.str_schema()),
            python_schema=core_schema.is_instance_schema(enum_type),
        )
    elif issubclass(enum_type, float):
        updates['type'] = 'numeric'
        lax = core_schema.chain_schema([core_schema.float_schema(), to_enum_validator])
        strict = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(to_enum, core_schema.float_schema()),
            python_schema=core_schema.is_instance_schema(enum_type),
        )
    else:
        lax = to_enum_validator
        strict = core_schema.json_or_python_schema(
            json_schema=to_enum_validator, python_schema=core_schema.is_instance_schema(enum_type)
        )
    return core_schema.lax_or_strict_schema(
        lax_schema=lax,
        strict_schema=strict,
        ref=enum_ref,
        metadata=metadata,
    )


@slots_dataclass
class MetadataApplier:
    inner_core_schema: CoreSchema
    outer_core_schema: CoreSchema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.outer_core_schema

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(self.inner_core_schema)


@slots_dataclass
class DecimalValidator:
    gt: int | decimal.Decimal | None = None
    ge: int | decimal.Decimal | None = None
    lt: int | decimal.Decimal | None = None
    le: int | decimal.Decimal | None = None
    max_digits: int | None = None
    decimal_places: int | None = None
    multiple_of: int | decimal.Decimal | None = None
    allow_inf_nan: bool = False
    check_digits: bool = False
    strict: bool = False

    def __post_init__(self) -> None:
        self.check_digits = self.max_digits is not None or self.decimal_places is not None
        if self.check_digits and self.allow_inf_nan:
            raise ValueError('allow_inf_nan=True cannot be used with max_digits or decimal_places')

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        string_schema = handler(core_schema.str_schema())

        if handler.mode == 'validation':
            float_schema = handler(
                core_schema.float_schema(
                    allow_inf_nan=self.allow_inf_nan,
                    multiple_of=None if self.multiple_of is None else float(self.multiple_of),
                    le=None if self.le is None else float(self.le),
                    ge=None if self.ge is None else float(self.ge),
                    lt=None if self.lt is None else float(self.lt),
                    gt=None if self.gt is None else float(self.gt),
                )
            )
            return {'anyOf': [float_schema, string_schema]}
        else:
            return string_schema

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        primitive_type_union = [
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.str_schema(strip_whitespace=True),
        ]
        is_instance_schema = core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(
                decimal.Decimal, core_schema.union_schema(primitive_type_union)
            ),
            python_schema=core_schema.is_instance_schema(decimal.Decimal),
        )
        lax = core_schema.no_info_after_validator_function(
            self.validate,
            core_schema.union_schema(
                [is_instance_schema, *primitive_type_union],
                strict=True,
            ),
        )
        strict = core_schema.custom_error_schema(
            core_schema.no_info_after_validator_function(
                self.validate,
                is_instance_schema,
            ),
            custom_error_type='decimal_type',
            custom_error_message='Input should be a valid Decimal instance or decimal string in JSON',
        )
        return core_schema.lax_or_strict_schema(
            lax_schema=lax, strict_schema=strict, serialization=core_schema.to_string_ser_schema()
        )

    def validate(self, __input_value: int | float | str) -> decimal.Decimal:  # noqa: C901 (ignore complexity)
        if isinstance(__input_value, decimal.Decimal):
            value = __input_value
        else:
            try:
                value = decimal.Decimal(str(__input_value))
            except decimal.DecimalException:
                raise PydanticCustomError('decimal_parsing', 'Input should be a valid decimal')

        if not self.allow_inf_nan or self.check_digits:
            _1, digit_tuple, exponent = value.as_tuple()
            if not self.allow_inf_nan and exponent in {'F', 'n', 'N'}:
                raise PydanticKnownError('finite_number')

            if self.check_digits:
                if isinstance(exponent, str):
                    raise PydanticKnownError('finite_number')
                elif exponent >= 0:
                    # A positive exponent adds that many trailing zeros.
                    digits = len(digit_tuple) + exponent
                    decimals = 0
                else:
                    # If the absolute value of the negative exponent is larger than the
                    # number of digits, then it's the same as the number of digits,
                    # because it'll consume all the digits in digit_tuple and then
                    # add abs(exponent) - len(digit_tuple) leading zeros after the
                    # decimal point.
                    if abs(exponent) > len(digit_tuple):
                        digits = decimals = abs(exponent)
                    else:
                        digits = len(digit_tuple)
                        decimals = abs(exponent)

                if self.max_digits is not None and digits > self.max_digits:
                    raise PydanticCustomError(
                        'decimal_max_digits',
                        'ensure that there are no more than {max_digits} digits in total',
                        {'max_digits': self.max_digits},
                    )

                if self.decimal_places is not None and decimals > self.decimal_places:
                    raise PydanticCustomError(
                        'decimal_max_places',
                        'ensure that there are no more than {decimal_places} decimal places',
                        {'decimal_places': self.decimal_places},
                    )

                if self.max_digits is not None and self.decimal_places is not None:
                    whole_digits = digits - decimals
                    expected = self.max_digits - self.decimal_places
                    if whole_digits > expected:
                        raise PydanticCustomError(
                            'decimal_whole_digits',
                            'ensure that there are no more than {whole_digits} digits before the decimal point',
                            {'whole_digits': expected},
                        )

        if self.multiple_of is not None:
            mod = value / self.multiple_of % 1
            if mod != 0:
                raise PydanticCustomError(
                    'decimal_multiple_of',
                    'Input should be a multiple of {multiple_of}',
                    {'multiple_of': self.multiple_of},
                )

        # these type checks are here to handle the following error:
        # Operator ">" not supported for types "(
        #   <subclass of int and Decimal>
        #   | <subclass of float and Decimal>
        #   | <subclass of str and Decimal>
        #   | Decimal" and "int
        #   | Decimal"
        # )
        if self.gt is not None and not value > self.gt:  # type: ignore
            raise PydanticKnownError('greater_than', {'gt': self.gt})
        elif self.ge is not None and not value >= self.ge:  # type: ignore
            raise PydanticKnownError('greater_than_equal', {'ge': self.ge})

        if self.lt is not None and not value < self.lt:  # type: ignore
            raise PydanticKnownError('less_than', {'lt': self.lt})
        if self.le is not None and not value <= self.le:  # type: ignore
            raise PydanticKnownError('less_than_equal', {'le': self.le})

        return value


def decimal_prepare_pydantic_annotations(source: Any, annotations: Iterable[Any]) -> list[Any] | None:
    if source is not decimal.Decimal:
        return None

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(
        metadata, {*_known_annotated_metadata.FLOAT_CONSTRAINTS, 'max_digits', 'decimal_places'}, decimal.Decimal
    )
    return [decimal.Decimal, DecimalValidator(**metadata), *remaining_annotations]


@slots_dataclass
class InnerSchemaValidator:
    """Use a fixed CoreSchema, avoiding interference from outward annotations"""

    core_schema: CoreSchema
    js_schema: JsonSchemaValue | None = None
    js_core_schema: CoreSchema | None = None
    js_schema_update: JsonSchemaValue | None = None

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        if self.js_schema is not None:
            return self.js_schema
        js_schema = handler(self.js_core_schema or self.core_schema)
        if self.js_schema_update is not None:
            js_schema.update(self.js_schema_update)
        return js_schema

    def __get_pydantic_core_schema__(self, source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.core_schema


def datetime_prepare_pydantic_annotations(source_type: Any, annotations: Iterable[Any]) -> list[Any] | None:
    import datetime

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    if source_type is datetime.date:
        sv = InnerSchemaValidator(core_schema.date_schema(**metadata))
    elif source_type is datetime.datetime:
        sv = InnerSchemaValidator(core_schema.datetime_schema(**metadata))
    elif source_type is datetime.time:
        sv = InnerSchemaValidator(core_schema.time_schema(**metadata))
    elif source_type is datetime.timedelta:
        sv = InnerSchemaValidator(core_schema.timedelta_schema(**metadata))
    else:
        return None
    # check now that we know the source type is correct
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.DATE_TIME_CONSTRAINTS, source_type)
    return [source_type, sv, *remaining_annotations]


def uuid_prepare_pydantic_annotations(source_type: Any, annotations: Iterable[Any]) -> list[Any] | None:
    # UUIDs have no constraints - they are fixed length, constructing a UUID instance checks the length

    from uuid import UUID

    if source_type is not UUID:
        return None

    def uuid_validator(input_value: str | bytes | UUID) -> UUID:
        if isinstance(input_value, UUID):
            return input_value
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
            raise PydanticCustomError('uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID')

    from_primitive_type_schema = core_schema.no_info_after_validator_function(
        uuid_validator, core_schema.union_schema([core_schema.str_schema(), core_schema.bytes_schema()])
    )
    lax = core_schema.json_or_python_schema(
        json_schema=from_primitive_type_schema,
        python_schema=core_schema.union_schema(
            [core_schema.is_instance_schema(UUID), from_primitive_type_schema],
        ),
    )

    strict = core_schema.json_or_python_schema(
        json_schema=from_primitive_type_schema,
        python_schema=core_schema.is_instance_schema(UUID),
    )

    schema = core_schema.lax_or_strict_schema(
        lax_schema=lax,
        strict_schema=strict,
        serialization=core_schema.to_string_ser_schema(),
    )

    return [
        source_type,
        InnerSchemaValidator(schema, js_core_schema=core_schema.str_schema(), js_schema_update={'format': 'uuid'}),
        *annotations,
    ]


def path_schema_prepare_pydantic_annotations(source_type: Any, annotations: Iterable[Any]) -> list[Any] | None:
    import pathlib

    if source_type not in {
        os.PathLike,
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
    }:
        return None

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.STR_CONSTRAINTS, source_type)

    construct_path = pathlib.PurePath if source_type is os.PathLike else source_type

    def path_validator(input_value: str) -> os.PathLike[Any]:
        try:
            return construct_path(input_value)  # type: ignore
        except TypeError as e:
            raise PydanticCustomError('path_type', 'Input is not a valid path') from e

    constrained_str_schema = core_schema.str_schema(**metadata)

    instance_schema = core_schema.json_or_python_schema(
        json_schema=core_schema.no_info_after_validator_function(path_validator, constrained_str_schema),
        python_schema=core_schema.is_instance_schema(source_type),
    )

    schema = core_schema.lax_or_strict_schema(
        lax_schema=core_schema.union_schema(
            [
                instance_schema,
                core_schema.no_info_after_validator_function(path_validator, constrained_str_schema),
            ],
            custom_error_type='path_type',
            custom_error_message='Input is not a valid path',
            strict=True,
        ),
        strict_schema=instance_schema,
        serialization=core_schema.to_string_ser_schema(),
    )

    return [
        source_type,
        InnerSchemaValidator(schema, js_core_schema=constrained_str_schema, js_schema_update={'format': 'path'}),
        *remaining_annotations,
    ]


@slots_dataclass
class SequenceValidator:
    mapped_origin: type[Any]
    item_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool = False
    js_core_schema: CoreSchema | None = None

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        assert self.js_core_schema is not None
        return handler(self.js_core_schema)

    def serialize_sequence_via_list(
        self, v: Any, handler: core_schema.SerializerFunctionWrapHandler, info: core_schema.SerializationInfo
    ) -> Any:
        items: list[Any] = []
        for index, item in enumerate(v):
            try:
                v = handler(item, index)
            except PydanticOmit:
                pass
            else:
                items.append(v)

        if info.mode_is_json():
            return items
        else:
            return self.mapped_origin(items)

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if self.item_source_type is Any:
            items_schema = None
        else:
            items_schema = handler.generate_schema(self.item_source_type)

        metadata = {'min_length': self.min_length, 'max_length': self.max_length, 'strict': self.strict}

        if self.mapped_origin in (list, set, frozenset):
            if self.mapped_origin is list:
                constrained_schema = core_schema.list_schema(items_schema, **metadata)
            elif self.mapped_origin is set:
                constrained_schema = core_schema.set_schema(items_schema, **metadata)
            else:
                assert self.mapped_origin is frozenset  # safety check in case we forget to add a case
                constrained_schema = core_schema.frozenset_schema(items_schema, **metadata)

            force_instance = None
            coerce_instance_wrap = identity

            serialization = None
        else:
            # safety check in case we forget to add a case
            assert self.mapped_origin in (collections.deque, collections.Counter)
            constrained_schema = core_schema.list_schema(items_schema, **metadata)
            if metadata.get('strict', False):
                force_instance = core_schema.json_or_python_schema(
                    json_schema=core_schema.list_schema(),
                    python_schema=core_schema.is_instance_schema(self.mapped_origin),
                )
            else:
                force_instance = None
            coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)

            serialization = core_schema.wrap_serializer_function_ser_schema(
                self.serialize_sequence_via_list, schema=items_schema or core_schema.any_schema(), info_arg=True
            )

        if force_instance:
            schema = core_schema.chain_schema([force_instance, coerce_instance_wrap(constrained_schema)])
        else:
            schema = coerce_instance_wrap(constrained_schema)

        if serialization:
            schema['serialization'] = serialization

        self.js_core_schema = constrained_schema

        return schema


SEQUENCE_ORIGIN_MAP: dict[Any, Any] = {
    typing.Deque: collections.deque,
    collections.deque: collections.deque,
    list: list,
    typing.List: list,
    set: set,
    typing.AbstractSet: set,
    typing.Set: set,
    frozenset: frozenset,
    typing.FrozenSet: frozenset,
    typing.Sequence: list,
    typing.MutableSequence: list,
}


MAPPING_ORIGIN_MAP: dict[Any, Any] = {
    typing.OrderedDict: collections.OrderedDict,
    typing.Dict: dict,
    typing.Mapping: dict,
    typing.MutableMapping: dict,
    typing.AbstractSet: set,
    typing.Set: set,
    typing.FrozenSet: frozenset,
    typing.Sequence: list,
    typing.MutableSequence: list,
    collections.Counter: collections.Counter,
}


def identity(s: CoreSchema) -> CoreSchema:
    return s


def sequence_like_prepare_pydantic_annotations(source_type: Any, annotations: Iterable[Any]) -> list[Any] | None:
    origin: Any = get_origin(source_type)

    mapped_origin = SEQUENCE_ORIGIN_MAP.get(origin, None) if origin else SEQUENCE_ORIGIN_MAP.get(source_type, None)
    if mapped_origin is None:
        return None

    args = get_args(source_type)

    if not args:
        args = (Any,)
    else:
        if len(args) != 1:
            raise ValueError('Expected sequence to have exactly 1 generic parameter')

    item_source_type = args[0]

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.SEQUENCE_CONSTRAINTS, source_type)

    return [source_type, SequenceValidator(mapped_origin, item_source_type, **metadata), *remaining_annotations]


def _ordered_dict_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_wrap_validator_function(
            _validators.ordered_dict_any_validator, core_schema.dict_schema()
        ),
        strict_schema=core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(OrderedDict, core_schema.dict_schema()),
            python_schema=core_schema.is_instance_schema(OrderedDict),
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
            lax_schema=core_schema.no_info_after_validator_function(
                _validators.ordered_dict_typed_validator,
                core_schema.dict_schema(
                    schema_generator.generate_schema(keys_arg), schema_generator.generate_schema(values_arg)
                ),
            ),
            strict_schema=core_schema.json_or_python_schema(
                json_schema=core_schema.no_info_after_validator_function(
                    OrderedDict, core_schema.dict_schema(inner_schema)
                ),
                python_schema=core_schema.no_info_after_validator_function(
                    OrderedDict,
                    core_schema.chain_schema(
                        [core_schema.is_instance_schema(OrderedDict), core_schema.dict_schema(inner_schema)]
                    ),
                ),
            ),
        )


def make_strict_ip_schema(tp: type[Any], metadata: Any) -> CoreSchema:
    return core_schema.json_or_python_schema(
        json_schema=core_schema.no_info_after_validator_function(tp, core_schema.str_schema()),
        python_schema=core_schema.is_instance_schema(tp),
        metadata=metadata,
    )


@schema_function(IPv4Address)
def ip_v4_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv4'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(_validators.ip_v4_address_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv4Address, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv4Interface)
def ip_v4_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv4interface'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(
            _validators.ip_v4_interface_validator, metadata=metadata
        ),
        strict_schema=make_strict_ip_schema(IPv4Interface, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv4Network)
def ip_v4_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv4network'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(_validators.ip_v4_network_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv4Network, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Address)
def ip_v6_address_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv6'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(_validators.ip_v6_address_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv6Address, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Interface)
def ip_v6_interface_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv6interface'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(
            _validators.ip_v6_interface_validator, metadata=metadata
        ),
        strict_schema=make_strict_ip_schema(IPv6Interface, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(IPv6Network)
def ip_v6_network_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'ipv6network'}])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_plain_validator_function(_validators.ip_v6_network_validator, metadata=metadata),
        strict_schema=make_strict_ip_schema(IPv6Network, metadata=metadata),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(Url)
def url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    return {'type': 'url'}


@schema_function(MultiHostUrl)
def multi_host_url_schema(_schema_generator: GenerateSchema, _obj: Any) -> core_schema.CoreSchema:
    return {'type': 'multi-host-url'}
