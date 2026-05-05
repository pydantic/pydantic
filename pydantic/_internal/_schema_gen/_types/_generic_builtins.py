"""Type handlers for generic built-in types, such as `list`, `dict`, etc."""

from __future__ import annotations

import collections.abc
from typing import Any, TypeVar

import annotated_types as at
import pydantic_core.core_schema as cs
from pydantic_core import CoreSchema
from typing_extensions import is_typeddict
from typing_inspection import typing_objects

from pydantic import FailFast, Strict

from .._conditions import TypeIs
from .._type_handlers import StdlibGenericTypeHandler
from .._type_registry import pydantic_registry


_T = TypeVar('_T')


@pydantic_registry.register(condition=TypeIs(list))
class ListTypeHandler(StdlibGenericTypeHandler):
    known_metadata = {at.MinLen, at.MaxLen, Strict, FailFast}
    parameters = (_T,)

    def handle_type(self, type: type[list], args: tuple[Any]) -> CoreSchema:
        arg = args[0]
        if arg is _T:
            items_schema = cs.any_schema()
        else:
            items_schema = self.generate_schema.generate_schema(arg)

        return cs.list_schema(items_schema)


_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


@pydantic_registry.register(condition=TypeIs(dict))
class DictTypeHandler(StdlibGenericTypeHandler):
    known_metadata = {at.MinLen, at.MaxLen, Strict}
    parameters = (_KT, _VT)

    def handle_type(
        self, type: type[dict], args: tuple[Any, Any]
    ) -> CoreSchema:
        keys_type, values_type = args
        keys_schema = cs.any_schema() if keys_type is _KT else self.generate_schema.generate_schema(keys_type)
        values_schema = cs.any_schema() if values_type is _VT else self.generate_schema.generate_schema(values_type)

        return cs.dict_schema(keys_schema=keys_schema, values_schema=values_schema)


import dataclasses
import os
import re
from enum import EnumMeta

from ..._generate_schema import VALIDATE_CALL_SUPPORTED_TYPES
from .._conditions import Predicate


@pydantic_registry.register(condition=TypeIs(tuple))
@pydantic_registry.register(condition=TypeIs(set))
@pydantic_registry.register(condition=TypeIs(collections.abc.MutableSet))
@pydantic_registry.register(condition=TypeIs(frozenset))
@pydantic_registry.register(condition=TypeIs(collections.abc.Set))
@pydantic_registry.register(condition=TypeIs(collections.abc.Sequence))
@pydantic_registry.register(condition=TypeIs(collections.abc.Iterable))
@pydantic_registry.register(condition=TypeIs(collections.abc.Generator))
@pydantic_registry.register(condition=TypeIs(type))
@pydantic_registry.register(condition=TypeIs(os.PathLike))
@pydantic_registry.register(condition=TypeIs(collections.abc.Mapping))
@pydantic_registry.register(condition=TypeIs(collections.abc.MutableMapping))
@pydantic_registry.register(condition=TypeIs(collections.OrderedDict))
@pydantic_registry.register(condition=TypeIs(collections.defaultdict))
@pydantic_registry.register(condition=TypeIs(collections.Counter))
@pydantic_registry.register(condition=TypeIs(collections.deque))
@pydantic_registry.register(condition=TypeIs(collections.abc.Callable))
@pydantic_registry.register(condition=TypeIs(re.Pattern))
@pydantic_registry.register(condition=Predicate(dataclasses.is_dataclass))
@pydantic_registry.register(condition=Predicate(typing_objects.is_typealiastype))
@pydantic_registry.register(condition=Predicate(is_typeddict))
@pydantic_registry.register(condition=Predicate(typing_objects.is_namedtuple))
@pydantic_registry.register(condition=Predicate(typing_objects.is_newtype))
@pydantic_registry.register(condition=Predicate(lambda tp: isinstance(tp, VALIDATE_CALL_SUPPORTED_TYPES)))
@pydantic_registry.register(condition=Predicate(lambda tp: isinstance(tp, EnumMeta)))
class PlaceholderGenericTypeHandler(StdlibGenericTypeHandler):
    known_metadata = set()

    def handle_type(self, type: Any, args: tuple[Any, ...]) -> CoreSchema:
        raise NotImplementedError
