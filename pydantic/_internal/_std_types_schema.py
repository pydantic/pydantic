"""Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

from __future__ import annotations as _annotations

import collections
import collections.abc
import dataclasses
import decimal
import os
import typing
from functools import partial
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, Callable, Iterable, Tuple, TypeVar

import typing_extensions
from pydantic_core import (
    CoreSchema,
    MultiHostUrl,
    PydanticCustomError,
    PydanticOmit,
    Url,
    core_schema,
)
from typing_extensions import get_args, get_origin

from pydantic.errors import PydanticSchemaGenerationError
from pydantic.fields import FieldInfo
from pydantic.types import Strict

from ..config import ConfigDict
from ..json_schema import JsonSchemaValue
from . import _known_annotated_metadata, _typing_extra
from ._internal_dataclass import slots_true
from ._schema_generation_shared import GetCoreSchemaHandler, GetJsonSchemaHandler

if typing.TYPE_CHECKING:
    from ._generate_schema import GenerateSchema

    StdSchemaFunction = Callable[[GenerateSchema, type[Any]], core_schema.CoreSchema]


@dataclasses.dataclass(**slots_true)
class SchemaTransformer:
    get_core_schema: Callable[[Any, GetCoreSchemaHandler], CoreSchema]
    get_json_schema: Callable[[CoreSchema, GetJsonSchemaHandler], JsonSchemaValue]

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.get_core_schema(source_type, handler)

    def __get_pydantic_json_schema__(self, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return self.get_json_schema(schema, handler)


@dataclasses.dataclass(**slots_true)
class InnerSchemaValidator:
    """Use a fixed CoreSchema, avoiding interference from outward annotations."""

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

    def __get_pydantic_core_schema__(self, _source_type: Any, _handler: GetCoreSchemaHandler) -> CoreSchema:
        return self.core_schema


def decimal_prepare_pydantic_annotations(
    source: Any, annotations: Iterable[Any], config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    if source is not decimal.Decimal:
        return None

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)

    config_allow_inf_nan = config.get('allow_inf_nan')
    if config_allow_inf_nan is not None:
        metadata.setdefault('allow_inf_nan', config_allow_inf_nan)

    _known_annotated_metadata.check_metadata(
        metadata, {*_known_annotated_metadata.FLOAT_CONSTRAINTS, 'max_digits', 'decimal_places'}, decimal.Decimal
    )
    return source, [InnerSchemaValidator(core_schema.decimal_schema(**metadata)), *remaining_annotations]


def datetime_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
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
    return (source_type, [sv, *remaining_annotations])


def uuid_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    # UUIDs have no constraints - they are fixed length, constructing a UUID instance checks the length

    from uuid import UUID

    if source_type is not UUID:
        return None

    return (source_type, [InnerSchemaValidator(core_schema.uuid_schema()), *annotations])


def path_schema_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    import pathlib

    orig_source_type: Any = get_origin(source_type) or source_type
    if (
        (source_type_args := get_args(source_type))
        and orig_source_type is os.PathLike
        and source_type_args[0] not in {str, bytes, Any}
    ):
        return None

    if orig_source_type not in {
        os.PathLike,
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
    }:
        return None

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.STR_CONSTRAINTS, orig_source_type)

    is_first_arg_byte = source_type_args and source_type_args[0] is bytes
    construct_path = pathlib.PurePath if orig_source_type is os.PathLike else orig_source_type
    constrained_schema = (
        core_schema.bytes_schema(**metadata) if is_first_arg_byte else core_schema.str_schema(**metadata)
    )

    def path_validator(input_value: str | bytes) -> os.PathLike[Any]:  # type: ignore
        try:
            if is_first_arg_byte:
                if isinstance(input_value, bytes):
                    try:
                        input_value = input_value.decode()
                    except UnicodeDecodeError as e:
                        raise PydanticCustomError('bytes_type', 'Input must be valid bytes') from e
                else:
                    raise PydanticCustomError('bytes_type', 'Input must be bytes')
            elif not isinstance(input_value, str):
                raise PydanticCustomError('path_type', 'Input is not a valid path')

            return construct_path(input_value)
        except TypeError as e:
            raise PydanticCustomError('path_type', 'Input is not a valid path') from e

    instance_schema = core_schema.json_or_python_schema(
        json_schema=core_schema.no_info_after_validator_function(path_validator, constrained_schema),
        python_schema=core_schema.is_instance_schema(orig_source_type),
    )

    strict: bool | None = None
    for annotation in annotations:
        if isinstance(annotation, Strict):
            strict = annotation.strict

    schema = core_schema.lax_or_strict_schema(
        lax_schema=core_schema.union_schema(
            [
                instance_schema,
                core_schema.no_info_after_validator_function(path_validator, constrained_schema),
            ],
            custom_error_type='path_type',
            custom_error_message=f'Input is not a valid path for {orig_source_type}',
            strict=True,
        ),
        strict_schema=instance_schema,
        serialization=core_schema.to_string_ser_schema(),
        strict=strict,
    )

    return (
        orig_source_type,
        [
            InnerSchemaValidator(schema, js_core_schema=constrained_schema, js_schema_update={'format': 'path'}),
            *remaining_annotations,
        ],
    )


def dequeue_validator(
    input_value: Any, handler: core_schema.ValidatorFunctionWrapHandler, maxlen: None | int
) -> collections.deque[Any]:
    if isinstance(input_value, collections.deque):
        maxlens = [v for v in (input_value.maxlen, maxlen) if v is not None]
        if maxlens:
            maxlen = min(maxlens)
        return collections.deque(handler(input_value), maxlen=maxlen)
    else:
        return collections.deque(handler(input_value), maxlen=maxlen)


def serialize_sequence_via_list(
    v: Any, handler: core_schema.SerializerFunctionWrapHandler, info: core_schema.SerializationInfo
) -> Any:
    items: list[Any] = []

    mapped_origin = SEQUENCE_ORIGIN_MAP.get(type(v), None)
    if mapped_origin is None:
        # we shouldn't hit this branch, should probably add a serialization error or something
        return v

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
        return mapped_origin(items)


@dataclasses.dataclass(**slots_true)
class SequenceValidator:
    mapped_origin: type[Any]
    item_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool | None = None
    fail_fast: bool | None = None

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if self.item_source_type is Any:
            items_schema = None
        else:
            items_schema = handler.generate_schema(self.item_source_type)

        metadata = {
            'min_length': self.min_length,
            'max_length': self.max_length,
            'strict': self.strict,
            'fail_fast': self.fail_fast,
        }

        if self.mapped_origin in (list, set, frozenset):
            if self.mapped_origin is list:
                constrained_schema = core_schema.list_schema(items_schema, **metadata)
            elif self.mapped_origin is set:
                constrained_schema = core_schema.set_schema(items_schema, **metadata)
            else:
                assert self.mapped_origin is frozenset  # safety check in case we forget to add a case
                constrained_schema = core_schema.frozenset_schema(items_schema, **metadata)

            schema = constrained_schema
        else:
            # safety check in case we forget to add a case
            assert self.mapped_origin in (collections.deque, collections.Counter)

            if self.mapped_origin is collections.deque:
                # if we have a MaxLen annotation might as well set that as the default maxlen on the deque
                # this lets us re-use existing metadata annotations to let users set the maxlen on a dequeue
                # that e.g. comes from JSON
                coerce_instance_wrap = partial(
                    core_schema.no_info_wrap_validator_function,
                    partial(dequeue_validator, maxlen=metadata.get('max_length', None)),
                )
            else:
                coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)

            # we have to use a lax list schema here, because we need to validate the deque's
            # items via a list schema, but it's ok if the deque itself is not a list (same for Counter)
            metadata_with_strict_override = {**metadata, 'strict': False}
            constrained_schema = core_schema.list_schema(items_schema, **metadata_with_strict_override)

            check_instance = core_schema.json_or_python_schema(
                json_schema=core_schema.list_schema(),
                python_schema=core_schema.is_instance_schema(self.mapped_origin),
            )

            serialization = core_schema.wrap_serializer_function_ser_schema(
                serialize_sequence_via_list, schema=items_schema or core_schema.any_schema(), info_arg=True
            )

            strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])

            if metadata.get('strict', False):
                schema = strict
            else:
                lax = coerce_instance_wrap(constrained_schema)
                schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
            schema['serialization'] = serialization

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
    typing.MutableSet: set,
    # this doesn't handle subclasses of these
    # parametrized typing.Set creates one of these
    collections.abc.MutableSet: set,
    collections.abc.Set: frozenset,
}


def sequence_like_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    origin: Any = get_origin(source_type)

    mapped_origin = SEQUENCE_ORIGIN_MAP.get(origin, None) if origin else SEQUENCE_ORIGIN_MAP.get(source_type, None)
    if mapped_origin is None:
        return None

    args = get_args(source_type)

    if not args:
        args = typing.cast(Tuple[Any], (Any,))
    elif len(args) != 1:
        raise ValueError('Expected sequence to have exactly 1 generic parameter')

    item_source_type = args[0]

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.SEQUENCE_CONSTRAINTS, source_type)

    return (source_type, [SequenceValidator(mapped_origin, item_source_type, **metadata), *remaining_annotations])


MAPPING_ORIGIN_MAP: dict[Any, Any] = {
    typing.DefaultDict: collections.defaultdict,
    collections.defaultdict: collections.defaultdict,
    collections.OrderedDict: collections.OrderedDict,
    typing_extensions.OrderedDict: collections.OrderedDict,
    dict: dict,
    typing.Dict: dict,
    collections.Counter: collections.Counter,
    typing.Counter: collections.Counter,
    # this doesn't handle subclasses of these
    typing.Mapping: dict,
    typing.MutableMapping: dict,
    # parametrized typing.{Mutable}Mapping creates one of these
    collections.abc.MutableMapping: dict,
    collections.abc.Mapping: dict,
}


def defaultdict_validator(
    input_value: Any, handler: core_schema.ValidatorFunctionWrapHandler, default_default_factory: Callable[[], Any]
) -> collections.defaultdict[Any, Any]:
    if isinstance(input_value, collections.defaultdict):
        default_factory = input_value.default_factory
        return collections.defaultdict(default_factory, handler(input_value))
    else:
        return collections.defaultdict(default_default_factory, handler(input_value))


def get_defaultdict_default_default_factory(values_source_type: Any) -> Callable[[], Any]:
    def infer_default() -> Callable[[], Any]:
        allowed_default_types: dict[Any, Any] = {
            typing.Tuple: tuple,
            tuple: tuple,
            collections.abc.Sequence: tuple,
            collections.abc.MutableSequence: list,
            typing.List: list,
            list: list,
            typing.Sequence: list,
            typing.Set: set,
            set: set,
            typing.MutableSet: set,
            collections.abc.MutableSet: set,
            collections.abc.Set: frozenset,
            typing.MutableMapping: dict,
            typing.Mapping: dict,
            collections.abc.Mapping: dict,
            collections.abc.MutableMapping: dict,
            float: float,
            int: int,
            str: str,
            bool: bool,
        }
        values_type_origin = get_origin(values_source_type) or values_source_type
        instructions = 'set using `DefaultDict[..., Annotated[..., Field(default_factory=...)]]`'
        if isinstance(values_type_origin, TypeVar):

            def type_var_default_factory() -> None:
                raise RuntimeError(
                    'Generic defaultdict cannot be used without a concrete value type or an'
                    ' explicit default factory, ' + instructions
                )

            return type_var_default_factory
        elif values_type_origin not in allowed_default_types:
            # a somewhat subjective set of types that have reasonable default values
            allowed_msg = ', '.join([t.__name__ for t in set(allowed_default_types.values())])
            raise PydanticSchemaGenerationError(
                f'Unable to infer a default factory for keys of type {values_source_type}.'
                f' Only {allowed_msg} are supported, other types require an explicit default factory'
                ' ' + instructions
            )
        return allowed_default_types[values_type_origin]

    # Assume Annotated[..., Field(...)]
    if _typing_extra.is_annotated(values_source_type):
        field_info = next((v for v in get_args(values_source_type) if isinstance(v, FieldInfo)), None)
    else:
        field_info = None
    if field_info and field_info.default_factory:
        default_default_factory = field_info.default_factory
    else:
        default_default_factory = infer_default()
    return default_default_factory


@dataclasses.dataclass(**slots_true)
class MappingValidator:
    mapped_origin: type[Any]
    keys_source_type: type[Any]
    values_source_type: type[Any]
    min_length: int | None = None
    max_length: int | None = None
    strict: bool = False

    def serialize_mapping_via_dict(self, v: Any, handler: core_schema.SerializerFunctionWrapHandler) -> Any:
        return handler(v)

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if self.keys_source_type is Any:
            keys_schema = None
        else:
            keys_schema = handler.generate_schema(self.keys_source_type)
        if self.values_source_type is Any:
            values_schema = None
        else:
            values_schema = handler.generate_schema(self.values_source_type)

        metadata = {'min_length': self.min_length, 'max_length': self.max_length, 'strict': self.strict}

        if self.mapped_origin is dict:
            schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
        else:
            constrained_schema = core_schema.dict_schema(keys_schema, values_schema, **metadata)
            check_instance = core_schema.json_or_python_schema(
                json_schema=core_schema.dict_schema(),
                python_schema=core_schema.is_instance_schema(self.mapped_origin),
            )

            if self.mapped_origin is collections.defaultdict:
                default_default_factory = get_defaultdict_default_default_factory(self.values_source_type)
                coerce_instance_wrap = partial(
                    core_schema.no_info_wrap_validator_function,
                    partial(defaultdict_validator, default_default_factory=default_default_factory),
                )
            else:
                coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, self.mapped_origin)

            serialization = core_schema.wrap_serializer_function_ser_schema(
                self.serialize_mapping_via_dict,
                schema=core_schema.dict_schema(
                    keys_schema or core_schema.any_schema(), values_schema or core_schema.any_schema()
                ),
                info_arg=False,
            )

            strict = core_schema.chain_schema([check_instance, coerce_instance_wrap(constrained_schema)])

            if metadata.get('strict', False):
                schema = strict
            else:
                lax = coerce_instance_wrap(constrained_schema)
                schema = core_schema.lax_or_strict_schema(lax_schema=lax, strict_schema=strict)
                schema['serialization'] = serialization

        return schema


def mapping_like_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    origin: Any = get_origin(source_type)

    mapped_origin = MAPPING_ORIGIN_MAP.get(origin, None) if origin else MAPPING_ORIGIN_MAP.get(source_type, None)
    if mapped_origin is None:
        return None

    args = get_args(source_type)

    if not args:
        args = typing.cast(Tuple[Any, Any], (Any, Any))
    elif mapped_origin is collections.Counter:
        # a single generic
        if len(args) != 1:
            raise ValueError('Expected Counter to have exactly 1 generic parameter')
        args = (args[0], int)  # keys are always an int
    elif len(args) != 2:
        raise ValueError('Expected mapping to have exactly 2 generic parameters')

    keys_source_type, values_source_type = args

    metadata, remaining_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    _known_annotated_metadata.check_metadata(metadata, _known_annotated_metadata.SEQUENCE_CONSTRAINTS, source_type)

    return (
        source_type,
        [
            MappingValidator(mapped_origin, keys_source_type, values_source_type, **metadata),
            *remaining_annotations,
        ],
    )


def ip_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    from ._validators import IP_VALIDATOR_LOOKUP

    if source_type not in [IPv4Address, IPv4Network, IPv4Interface, IPv6Address, IPv6Network, IPv6Interface]:
        return None

    ip_type_json_schema_format = {
        IPv4Address: 'ipv4',
        IPv4Network: 'ipv4network',
        IPv4Interface: 'ipv4interface',
        IPv6Address: 'ipv6',
        IPv6Network: 'ipv6network',
        IPv6Interface: 'ipv6interface',
    }

    return source_type, [
        SchemaTransformer(
            lambda _1, _2: core_schema.lax_or_strict_schema(
                lax_schema=core_schema.no_info_plain_validator_function(IP_VALIDATOR_LOOKUP[source_type]),
                strict_schema=core_schema.json_or_python_schema(
                    json_schema=core_schema.no_info_after_validator_function(source_type, core_schema.str_schema()),
                    python_schema=core_schema.is_instance_schema(source_type),
                ),
                serialization=core_schema.to_string_ser_schema(),
            ),
            lambda _1, _2: {'type': 'string', 'format': ip_type_json_schema_format[source_type]},
        ),
        *annotations,
    ]


def url_prepare_pydantic_annotations(
    source_type: Any, annotations: Iterable[Any], _config: ConfigDict
) -> tuple[Any, list[Any]] | None:
    if source_type is Url:
        return source_type, [
            SchemaTransformer(
                lambda _1, _2: core_schema.url_schema(),
                lambda cs, handler: handler(cs),
            ),
            *annotations,
        ]
    if source_type is MultiHostUrl:
        return source_type, [
            SchemaTransformer(
                lambda _1, _2: core_schema.multi_host_url_schema(),
                lambda cs, handler: handler(cs),
            ),
            *annotations,
        ]


PREPARE_METHODS: tuple[Callable[[Any, Iterable[Any], ConfigDict], tuple[Any, list[Any]] | None], ...] = (
    decimal_prepare_pydantic_annotations,
    sequence_like_prepare_pydantic_annotations,
    datetime_prepare_pydantic_annotations,
    uuid_prepare_pydantic_annotations,
    path_schema_prepare_pydantic_annotations,
    mapping_like_prepare_pydantic_annotations,
    ip_prepare_pydantic_annotations,
    url_prepare_pydantic_annotations,
)
