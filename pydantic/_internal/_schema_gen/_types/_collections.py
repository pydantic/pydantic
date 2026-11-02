"""Type handlers for collection types, such as `list`, `dict`, `collections.abc.Sequence`, etc."""

from __future__ import annotations

import collections
import collections.abc
import sys
import typing
import warnings
from functools import partial
from typing import Any

from pydantic_core import CoreSchema, core_schema
from typing_inspection import typing_objects

from ....types import FailFast, Strict
from ....warnings import UnsupportedFieldAttributeWarning
from ..._generics import get_standard_typevars_map, replace_types
from ..._utils import smart_deepcopy
from .._annotations_handler import AnnotationsHandler, apply_constraints
from .._conditions import TypeIs
from .._type_handlers import GenericTypeHandler
from .._type_registry import default_registry
from ._builtins import LENGTH

COLLECTION = LENGTH | {Strict, FailFast}


def _two_args(type: Any, args: tuple[Any, ...]) -> tuple[Any, Any]:
    if len(args) < 2:
        raise TypeError(f'Expected two type arguments for {type}, got 1')
    return args[0], args[1]


@default_registry.register
class ListTypeHandler(GenericTypeHandler):
    """Type handler for `list` and `collections.abc.MutableSequence`."""

    match_condition = TypeIs(list, collections.abc.MutableSequence)
    known_metadata = COLLECTION
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema: CoreSchema = {'type': 'list', 'items_schema': self.generate_schema(args[0])}
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class SetTypeHandler(GenericTypeHandler):
    """Type handler for `set` and `collections.abc.MutableSet`."""

    match_condition = TypeIs(set, collections.abc.MutableSet)
    known_metadata = COLLECTION
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema: CoreSchema = {'type': 'set', 'items_schema': self.generate_schema(args[0])}
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class FrozenSetTypeHandler(GenericTypeHandler):
    """Type handler for `frozenset` and `collections.abc.Set`."""

    match_condition = TypeIs(frozenset, collections.abc.Set)
    known_metadata = COLLECTION
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema: CoreSchema = {'type': 'frozenset', 'items_schema': self.generate_schema(args[0])}
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class DequeTypeHandler(GenericTypeHandler):
    """Type handler for `collections.deque`."""

    match_condition = TypeIs(collections.deque)
    known_metadata = COLLECTION
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints(core_schema.deque_schema(self.generate_schema(args[0])), annotations_handler)


@default_registry.register
class DictTypeHandler(GenericTypeHandler):
    """Type handler for `dict`."""

    match_condition = TypeIs(dict)
    known_metadata = COLLECTION
    default_args = (Any, Any)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        keys_type, values_type = _two_args(type, args)
        schema: CoreSchema = {
            'type': 'dict',
            'keys_schema': self.generate_schema(keys_type),
            'values_schema': self.generate_schema(values_type),
        }
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class OrderedDictTypeHandler(GenericTypeHandler):
    """Type handler for `collections.OrderedDict`."""

    match_condition = TypeIs(collections.OrderedDict)
    known_metadata = COLLECTION
    default_args = (Any, Any)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        keys_type, values_type = _two_args(type, args)
        schema = core_schema.ordered_dict_schema(self.generate_schema(keys_type), self.generate_schema(values_type))
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class CounterTypeHandler(GenericTypeHandler):
    """Type handler for `collections.Counter`."""

    match_condition = TypeIs(collections.Counter)
    known_metadata = COLLECTION
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = core_schema.counter_schema(self.generate_schema(args[0]), core_schema.int_schema())
        return apply_constraints(schema, annotations_handler)


if sys.version_info >= (3, 15):
    from builtins import frozendict

    @default_registry.register
    class FrozenDictTypeHandler(GenericTypeHandler):
        """Type handler for `frozendict`."""

        match_condition = TypeIs(frozendict)
        known_metadata = COLLECTION
        default_args = (Any, Any)

        def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
            keys_type, values_type = _two_args(type, args)
            schema = core_schema.frozendict_schema(self.generate_schema(keys_type), self.generate_schema(values_type))
            return apply_constraints(schema, annotations_handler)


TUPLE_TYPES: list[type] = [typing.Tuple, tuple]  # noqa: UP006


@default_registry.register
class TupleTypeHandler(GenericTypeHandler):
    """Type handler for `tuple`, e.g. `tuple[int, str]` or `tuple[int, ...]`."""

    match_condition = TypeIs(tuple)
    known_metadata = COLLECTION

    def _generate_schema(self, obj: Any, origin: Any | None, annotations_handler: AnnotationsHandler) -> CoreSchema:
        # The arguments are extracted here, as `tuple[()]` (no arguments) differs from `tuple` (unparameterized):
        # TODO: do we really need to resolve type vars here?
        typevars_map = get_standard_typevars_map(obj)
        params = self.schema_generator._get_args_resolving_forward_refs(obj)

        if typevars_map and params:
            params = tuple(replace_types(param, typevars_map) for param in params)
        return self.handle_type(obj, params or (), annotations_handler)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        # NOTE: subtle difference: `tuple[()]` gives `params=()`, whereas `typing.Tuple[()]` gives `params=((),)`
        # This is only true for <3.11, on Python 3.11+ `typing.Tuple[()]` gives `params=()`
        if not args:
            if type in TUPLE_TYPES:
                schema = core_schema.tuple_schema([core_schema.any_schema()], variadic_item_index=0)
            else:
                # special case for `tuple[()]` which means `tuple[]` - an empty tuple
                schema = core_schema.tuple_schema([])
        elif args[-1] is Ellipsis:
            if len(args) == 2:
                schema = core_schema.tuple_schema([self.generate_schema(args[0])], variadic_item_index=0)
            else:
                # TODO: something like https://github.com/pydantic/pydantic/issues/5952
                raise ValueError('Variable tuples can only have one type')
        elif len(args) == 1 and args[0] == ():
            # special case for `tuple[()]` which means `tuple[]` - an empty tuple
            # NOTE: This conditional can be removed when we drop support for Python 3.10.
            schema = core_schema.tuple_schema([])
        else:
            schema = core_schema.tuple_schema([self.generate_schema(param) for param in args])
        return apply_constraints(schema, annotations_handler)


@default_registry.register
class SequenceTypeHandler(GenericTypeHandler):
    """Type handler for `collections.abc.Sequence`."""

    match_condition = TypeIs(collections.abc.Sequence)
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        from ..._serializers import serialize_sequence_via_list

        items_type = args[0]
        item_type_schema = self.generate_schema(items_type)
        list_schema = core_schema.list_schema(item_type_schema)

        json_schema = smart_deepcopy(list_schema)
        python_schema = core_schema.is_instance_schema(typing.Sequence, cls_repr='Sequence')
        if not typing_objects.is_any(items_type):
            from ..._validators import sequence_validator

            python_schema = core_schema.chain_schema(
                [python_schema, core_schema.no_info_wrap_validator_function(sequence_validator, list_schema)],
            )

        serialization = core_schema.wrap_serializer_function_ser_schema(
            serialize_sequence_via_list, schema=item_type_schema, info_arg=True
        )
        return core_schema.json_or_python_schema(
            json_schema=json_schema, python_schema=python_schema, serialization=serialization
        )


@default_registry.register
class IterableTypeHandler(GenericTypeHandler):
    """Type handler for `collections.abc.Iterable` and `collections.abc.Generator`."""

    match_condition = TypeIs(collections.abc.Iterable, collections.abc.Generator)
    known_metadata = LENGTH
    default_args = (Any,)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints(core_schema.generator_schema(self.generate_schema(args[0])), annotations_handler)


@default_registry.register
class MappingTypeHandler(GenericTypeHandler):
    """Type handler for `collections.abc.Mapping`, `collections.abc.MutableMapping` and `collections.defaultdict`."""

    match_condition = TypeIs(collections.abc.Mapping, collections.abc.MutableMapping, collections.defaultdict)
    default_args = (Any, Any)

    def handle_type(self, type: Any, args: tuple[Any, ...], annotations_handler: AnnotationsHandler) -> CoreSchema:
        from ..._validators import MAPPING_ORIGIN_MAP, defaultdict_validator, get_defaultdict_default_default_factory

        tp = type
        keys_type, values_type = _two_args(type, args)
        mapped_origin = MAPPING_ORIGIN_MAP[tp]
        keys_schema = self.generate_schema(keys_type)
        with warnings.catch_warnings():
            # We kind of abused `Field()` default factories to be able to specify
            # the `defaultdict`'s `default_factory`. As a consequence, we get warnings
            # as normally `FieldInfo.default_factory` is unsupported in the context where
            # `Field()` is used and our only solution is to ignore them (note that this might
            # wrongfully ignore valid warnings, e.g. if the `value_type` is a PEP 695 type alias
            # with unsupported metadata).
            warnings.simplefilter('ignore', category=UnsupportedFieldAttributeWarning)
            values_schema = self.generate_schema(values_type)
        dict_schema = core_schema.dict_schema(keys_schema, values_schema, strict=False)

        if mapped_origin is dict:
            return dict_schema

        check_instance = core_schema.json_or_python_schema(
            json_schema=dict_schema,
            python_schema=core_schema.is_instance_schema(mapped_origin),
        )

        if tp is collections.defaultdict:
            default_default_factory = get_defaultdict_default_default_factory(values_type)
            coerce_instance_wrap = partial(
                core_schema.no_info_wrap_validator_function,
                partial(defaultdict_validator, default_default_factory=default_default_factory),
            )
        else:
            coerce_instance_wrap = partial(core_schema.no_info_after_validator_function, mapped_origin)

        lax_schema = coerce_instance_wrap(dict_schema)
        strict_schema = core_schema.chain_schema([check_instance, lax_schema])

        return core_schema.lax_or_strict_schema(
            lax_schema=lax_schema,
            strict_schema=strict_schema,
            serialization=core_schema.wrap_serializer_function_ser_schema(
                lambda v, h: h(v), schema=dict_schema, info_arg=False
            ),
        )
