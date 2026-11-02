"""Type handlers for (non-generic) built-in types, such as `int`, `str`, etc."""

from __future__ import annotations

from types import EllipsisType, NoneType
from typing import Any

import annotated_types as at
from pydantic_core import MISSING, CoreSchema

from ....types import AllowInfNan, Strict
from ... import _constraints as c
from .._annotations_handler import AnnotationsHandler, apply_constraints
from .._conditions import TypeIs, TypeIsTypingMember
from .._type_handlers import TypeHandler
from .._type_registry import default_registry

INEQUALITY = frozenset({at.Gt, at.Ge, at.Lt, at.Le})
NUMERIC = INEQUALITY | {at.MultipleOf}
LENGTH = frozenset({at.MinLen, at.MaxLen})


@default_registry.register
class IntTypeHandler(TypeHandler):
    """Type handler for the built-in `int` type."""

    match_condition = TypeIs(int)
    known_metadata = NUMERIC | {Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'int'}, annotations_handler)


@default_registry.register
class FloatTypeHandler(TypeHandler):
    """Type handler for the built-in `float` type."""

    match_condition = TypeIs(float)
    known_metadata = NUMERIC | {Strict, AllowInfNan}

    def handle_type(self, type: type[float], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'float'}, annotations_handler)


@default_registry.register
class StrTypeHandler(TypeHandler):
    """Type handler for the built-in `str` type."""

    match_condition = TypeIs(str)
    known_metadata = LENGTH | {
        Strict,
        c.Pattern,
        c.StripWhitespace,
        c.ToLower,
        c.ToUpper,
        c.AsciiOnly,
        c.CoerceNumbersToStr,
    }

    def handle_type(self, type: type[str], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'str'}, annotations_handler)


@default_registry.register
class BytesTypeHandler(TypeHandler):
    """Type handler for the built-in `bytes` type."""

    match_condition = TypeIs(bytes)
    known_metadata = LENGTH | {Strict}

    def handle_type(self, type: type[bytes], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'bytes'}, annotations_handler)


@default_registry.register
class BoolTypeHandler(TypeHandler):
    """Type handler for the built-in `bool` type."""

    match_condition = TypeIs(bool)
    known_metadata = frozenset({Strict})

    def handle_type(self, type: type[bool], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'bool'}, annotations_handler)


@default_registry.register
class ComplexTypeHandler(TypeHandler):
    """Type handler for the built-in `complex` type."""

    match_condition = TypeIs(complex)
    known_metadata = frozenset({Strict})

    def handle_type(self, type: type[complex], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return apply_constraints({'type': 'complex'}, annotations_handler)


@default_registry.register
class AnyTypeHandler(TypeHandler):
    """Type handler for the built-in `object` type and `typing.Any`."""

    match_condition = TypeIs(object) | TypeIsTypingMember('Any')

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return {'type': 'any'}


@default_registry.register
class NoneTypeHandler(TypeHandler):
    """Type handler for `None` and `types.NoneType`."""

    match_condition = TypeIs(None, NoneType)

    def handle_type(self, type: None | type[None], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return {'type': 'none'}


@default_registry.register
class EllipsisTypeHandler(TypeHandler):
    """Type handler for `types.EllipsisType`."""

    match_condition = TypeIs(EllipsisType)

    def handle_type(self, type: type[EllipsisType], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return {'type': 'ellipsis'}


@default_registry.register
class MissingTypeHandler(TypeHandler):
    """Type handler for the `MISSING` sentinel."""

    match_condition = TypeIs(MISSING)

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return {'type': 'missing-sentinel'}
