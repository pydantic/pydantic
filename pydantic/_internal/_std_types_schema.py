"""Logic for generating pydantic-core schemas for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

# TODO: working on removing these types as the annotation injection pattern we use here is inconsistent
# with the rest of the library and is not well supported by the pydantic-core schema generation

from __future__ import annotations as _annotations

import collections
import collections.abc
import dataclasses
import typing
from functools import partial
from typing import Any, Callable, Iterable, Tuple, TypeVar, cast

import typing_extensions
from pydantic_core import (
    CoreSchema,
    core_schema,
)
from typing_extensions import get_args, get_origin

from pydantic.errors import PydanticSchemaGenerationError

from . import _known_annotated_metadata, _typing_extra
from ._import_utils import import_cached_field_info
from ._internal_dataclass import slots_true
from ._schema_generation_shared import GetCoreSchemaHandler

FieldInfo = import_cached_field_info()


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
        # Assume the default factory does not take any argument:
        default_default_factory = cast(Callable[[], Any], field_info.default_factory)
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
        if _typing_extra.is_any(self.keys_source_type):
            keys_schema = None
        else:
            keys_schema = handler.generate_schema(self.keys_source_type)
        if _typing_extra.is_any(self.values_source_type):
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
    source_type: Any, annotations: Iterable[Any]
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
