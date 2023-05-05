"""
Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""
from __future__ import annotations as _annotations

import inspect
import typing
from collections import OrderedDict, deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from os import PathLike
from pathlib import PurePath
from typing import Any, Callable, Iterable
from uuid import UUID

from pydantic_core import CoreSchema, MultiHostUrl, PydanticCustomError, PydanticKnownError, Url, core_schema
from typing_extensions import get_args

from ..json_schema import JsonSchemaValue, update_json_schema
from . import _known_annotated_metadata, _serializers, _validators
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

    def to_enum(__input_value: Any, info: core_schema.ValidationInfo | None = None) -> Enum:
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

    to_enum_validator = core_schema.general_plain_validator_function(to_enum)
    if issubclass(enum_type, int):
        # this handles `IntEnum`, and also `Foobar(int, Enum)`
        updates['type'] = 'integer'
        lax = core_schema.chain_schema([core_schema.int_schema(), to_enum_validator])
        # Allow str from JSON to get better error messages (str will still fail validation in to_enum)
        # Disallow float from JSON due to strict mode
        strict = core_schema.is_instance_schema(enum_type, json_types={'int', 'str'}, json_function=to_enum)
    elif issubclass(enum_type, str):
        # this handles `StrEnum` (3.11 only), and also `Foobar(str, Enum)`
        updates['type'] = 'string'
        lax = core_schema.chain_schema([core_schema.str_schema(), to_enum_validator])
        # Allow all types from JSON to get better error messages (numeric types will still fail validation in to_enum)
        strict = core_schema.is_instance_schema(enum_type, json_types={'int', 'str', 'float'}, json_function=to_enum)
    elif issubclass(enum_type, float):
        updates['type'] = 'numeric'
        lax = core_schema.chain_schema([core_schema.float_schema(), to_enum_validator])
        # Allow str from JSON to get better error messages (str will still fail validation in to_enum)
        strict = core_schema.is_instance_schema(enum_type, json_types={'int', 'str', 'float'}, json_function=to_enum)
    else:
        lax = to_enum_validator
        strict = core_schema.is_instance_schema(enum_type, json_types={'float', 'int', 'str'}, json_function=to_enum)
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
    gt: int | Decimal | None = None
    ge: int | Decimal | None = None
    lt: int | Decimal | None = None
    le: int | Decimal | None = None
    max_digits: int | None = None
    decimal_places: int | None = None
    multiple_of: int | Decimal | None = None
    allow_inf_nan: bool = False
    check_digits: bool = False
    strict: bool = False

    def __post_init__(self) -> None:
        self.check_digits = self.max_digits is not None or self.decimal_places is not None
        if self.check_digits and self.allow_inf_nan:
            raise ValueError('allow_inf_nan=True cannot be used with max_digits or decimal_places')

    def __get_pydantic_json_schema__(self, _schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        json_schema = core_schema.float_schema(
            allow_inf_nan=self.allow_inf_nan,
            multiple_of=None if self.multiple_of is None else float(self.multiple_of),
            le=None if self.le is None else float(self.le),
            ge=None if self.ge is None else float(self.ge),
            lt=None if self.lt is None else float(self.lt),
            gt=None if self.gt is None else float(self.gt),
        )
        return handler(json_schema)

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        lax = core_schema.no_info_after_validator_function(
            self.validate,
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
            core_schema.no_info_after_validator_function(
                self.validate,
                core_schema.is_instance_schema(Decimal, json_types={'int', 'float'}),
            ),
            custom_error_type='decimal_type',
            custom_error_message='Input should be a valid Decimal instance or decimal string in JSON',
        )
        return core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)

    def validate(self, __input_value: int | float | str) -> Decimal:  # noqa: C901 (ignore complexity)
        if isinstance(__input_value, Decimal):
            value = __input_value
        else:
            try:
                value = Decimal(str(__input_value))
            except DecimalException:
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


def decimal_prepare_pydantic_annotations(_source: Any, annotations: Iterable[Any]) -> Iterable[Any]:
    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(
        metadata, {*_known_annotated_metadata.FLOAT_CONSTRAINTS, 'max_digits', 'decimal_places'}, Decimal
    )
    yield Decimal
    yield DecimalValidator(**metadata)
    yield from remaining_annotations


@schema_function(UUID)
def uuid_schema(_schema_generator: GenerateSchema, uuid_type: type[UUID]) -> core_schema.LaxOrStrictSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'uuid'}])
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    lax = core_schema.union_schema(
        [
            core_schema.is_instance_schema(uuid_type, json_types={'str'}),
            core_schema.no_info_after_validator_function(
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
                                core_schema.no_info_plain_validator_function(_validators.uuid_validator),
                            ]
                        ),
                    ]
                ),
            ],
            metadata=metadata,
        ),
        serialization=core_schema.to_string_ser_schema(),
    )


@schema_function(PurePath)
@schema_function(PathLike)
def path_schema(_schema_generator: GenerateSchema, path_type: type[PathLike]) -> core_schema.LaxOrStrictSchema:
    construct_path = PurePath if path_type is PathLike else path_type
    metadata = build_metadata_dict(js_functions=[lambda _c, _h: {'type': 'string', 'format': 'path'}])

    def path_validator(__input_value: str) -> PathLike:
        try:
            return construct_path(__input_value)  # type: ignore
        except TypeError as e:
            raise PydanticCustomError('path_type', 'Input is not a valid path') from e

    instance_schema = core_schema.is_instance_schema(path_type, json_types={'str'}, json_function=path_validator)

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


def _deque_ser_schema(
    inner_schema: core_schema.CoreSchema | None = None,
) -> core_schema.WrapSerializerFunctionSerSchema:
    return core_schema.wrap_serializer_function_ser_schema(
        _serializers.serialize_deque, info_arg=True, schema=inner_schema or core_schema.any_schema()
    )


def _deque_any_schema() -> core_schema.LaxOrStrictSchema:
    metadata = build_metadata_dict(js_functions=[lambda _c, h: h(core_schema.list_schema(core_schema.any_schema()))])
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_wrap_validator_function(
            _validators.deque_any_validator,
            core_schema.list_schema(),
        ),
        strict_schema=core_schema.general_after_validator_function(
            lambda x, _: x if isinstance(x, deque) else deque(x),
            core_schema.is_instance_schema(deque, json_types={'list'}),
        ),
        serialization=_deque_ser_schema(),
        metadata=metadata,
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
        metadata = build_metadata_dict(js_functions=[lambda _c, h: h(core_schema.list_schema(inner_schema))])
        lax_schema = core_schema.no_info_wrap_validator_function(
            _validators.deque_typed_validator,
            core_schema.list_schema(inner_schema, strict=False),
        )

        return core_schema.lax_or_strict_schema(
            lax_schema=lax_schema,
            strict_schema=core_schema.chain_schema(
                [core_schema.is_instance_schema(deque, json_types={'list'}), lax_schema],
            ),
            serialization=_deque_ser_schema(inner_schema),
            metadata=metadata,
        )


def _ordered_dict_any_schema() -> core_schema.LaxOrStrictSchema:
    return core_schema.lax_or_strict_schema(
        lax_schema=core_schema.no_info_wrap_validator_function(
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
            lax_schema=core_schema.no_info_after_validator_function(
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
