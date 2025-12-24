"""Type handlers for (non-generic) built-in types, such as `int`, `str`, etc."""

from __future__ import annotations

from typing import Any

import annotated_types as at
import pydantic_core.core_schema as cs
from pydantic_core import CoreSchema

from pydantic import Strict

from ... import _typing_extra
from .._conditions import TypeIs, TypeIsTypingMember
from .._type_handlers import TypeHandler
from .._type_registry import pydantic_registry



@pydantic_registry.register(condition=TypeIs(int))
class IntTypeHandler(TypeHandler):
    """Type handler for built-in type `int`."""

    # TODO: `_PydanticGeneralMetadata`
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int]) -> CoreSchema:
        return cs.int_schema()


@pydantic_registry.register(condition=TypeIs(float))
class FloatTypeHandler(TypeHandler):
    """Type handler for built-in type `float`."""

    # TODO: `_PydanticGeneralMetadata`
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int]) -> CoreSchema:
        return cs.float_schema()

@pydantic_registry.register(condition=TypeIs(str))
class StrTypeHandler(TypeHandler):
    """Type handler for built-in type `str`."""

    # TODO: strip_whitespace, to_lower, to_upper, pattern, coerce_numbers_to_str
    # (Currently as a single `_PydanticGeneralMetadata`).
    known_metadata = {at.MaxLen, at.MinLen, Strict}

    def handle_type(self, type: type[str]) -> CoreSchema:
        return cs.str_schema()


@pydantic_registry.register(condition=TypeIs(bytes))
class BytesTypeHandler(TypeHandler):
    """Type handler for built-in type `bytes`."""

    known_metadata = {at.MaxLen, at.MinLen, Strict}

    def handle_type(self, type: type[bytes]) -> CoreSchema:
        return cs.bytes_schema()


@pydantic_registry.register(condition=TypeIs(bool))
class BoolTypeHandler(TypeHandler):
    """Type handler for built-in type `bool`."""

    known_metadata = {Strict}

    def handle_type(self, type: type[bool]) -> CoreSchema:
        return cs.bool_schema()


@pydantic_registry.register(condition=TypeIs(complex))
class ComplexTypeHandler(TypeHandler):
    """Type handler for built-in type `complex`."""

    known_metadata = {Strict}

    def handle_type(self, type: type[bool]) -> CoreSchema:
        return cs.complex_schema()



# TODO: implement __or__ on conditions?
@pydantic_registry.register(condition=TypeIsTypingMember('Any'))
@pydantic_registry.register(condition=TypeIs(object))
class AnyOrObjectTypeHandler(TypeHandler):
    """Type handler for built-in type `object` or `typing.Any`."""

    known_metadata = set()

    def handle_type(self, type: Any) -> CoreSchema:
        return cs.any_schema()


@pydantic_registry.register(condition=TypeIs(None))
@pydantic_registry.register(condition=TypeIs(_typing_extra.NoneType))
class NoneTypeHandler(TypeHandler):
    """Type handler for the `None` object or the `types.NoneType` type."""

    known_metadata = set()

    def handle_type(self, type: None | type[None]) -> CoreSchema:
        return cs.none_schema()
