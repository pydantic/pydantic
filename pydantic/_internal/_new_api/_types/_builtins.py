"""Type handlers for (non-generic) built-in types, such as `int`, `str`, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import annotated_types as at
import pydantic_core.core_schema as cs
from pydantic_core import CoreSchema

from pydantic import Strict

from ... import _typing_extra
from .._conditions import TypeIs, TypeIsTypingMember
from .._type_handlers import TypeHandler
from .._type_registry import pydantic_registry

if TYPE_CHECKING:
    from .._annotations_handler import AnnotationsHandler


@pydantic_registry.register(condition=TypeIs(int))
class IntTypeHandler(TypeHandler):
    """Type handler for built-in type `int`."""

    # TODO: `_PydanticGeneralMetadata`
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.int_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, at.Gt):
                schema['gt'] = ann.gt
            elif isinstance(ann, at.Ge):
                schema['ge'] = ann.ge
            elif isinstance(ann, at.Lt):
                schema['lt'] = ann.lt
            elif isinstance(ann, at.Le):
                schema['le'] = ann.le
            elif isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


@pydantic_registry.register(condition=TypeIs(float))
class FloatTypeHandler(TypeHandler):
    """Type handler for built-in type `float`."""

    # TODO: `_PydanticGeneralMetadata`
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.float_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, at.Gt):
                schema['gt'] = ann.gt
            elif isinstance(ann, at.Ge):
                schema['ge'] = ann.ge
            elif isinstance(ann, at.Lt):
                schema['lt'] = ann.lt
            elif isinstance(ann, at.Le):
                schema['le'] = ann.le
            elif isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


@pydantic_registry.register(condition=TypeIs(str))
class StrTypeHandler(TypeHandler):
    """Type handler for built-in type `str`."""

    # TODO: strip_whitespace, to_lower, to_upper, pattern, coerce_numbers_to_str
    # (Currently as a single `_PydanticGeneralMetadata`).
    known_metadata = {at.MaxLen, at.MinLen, Strict}

    def handle_type(self, type: type[str], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.str_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, at.MaxLen):
                schema['max_length'] = ann.max_length
            elif isinstance(ann, at.MinLen):
                schema['min_length'] = ann.min_length
            elif isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


@pydantic_registry.register(condition=TypeIs(bytes))
class BytesTypeHandler(TypeHandler):
    """Type handler for built-in type `bytes`."""

    known_metadata = {at.MaxLen, at.MinLen, Strict}

    def handle_type(self, type: type[bytes], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.bytes_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, at.MaxLen):
                schema['max_length'] = ann.max_length
            elif isinstance(ann, at.MinLen):
                schema['min_length'] = ann.min_length
            elif isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


@pydantic_registry.register(condition=TypeIs(bool))
class BoolTypeHandler(TypeHandler):
    """Type handler for built-in type `bool`."""

    known_metadata = {Strict}

    def handle_type(self, type: type[bool], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.bool_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


@pydantic_registry.register(condition=TypeIs(complex))
class ComplexTypeHandler(TypeHandler):
    """Type handler for built-in type `complex`."""

    known_metadata = {Strict}

    def handle_type(self, type: type[bool], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.complex_schema()
        for ann in annotations_handler.iter_annotations():
            if isinstance(ann, Strict):
                schema['strict'] = ann.strict

        return schema


# TODO: implement __or__ on conditions?
@pydantic_registry.register(condition=TypeIsTypingMember('Any'))
@pydantic_registry.register(condition=TypeIs(object))
class AnyOrObjectTypeHandler(TypeHandler):
    """Type handler for built-in type `object` or `typing.Any`."""

    known_metadata = set()

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        return cs.any_schema()


@pydantic_registry.register(condition=TypeIs(None))
@pydantic_registry.register(condition=TypeIs(_typing_extra.NoneType))
class NoneTypeHandler(TypeHandler):
    """Type handler for the `None` object or the `types.NoneType` type."""

    known_metadata = set()

    def handle_type(self, type: None | type[None], annotations_handler: AnnotationsHandler) -> CoreSchema:
        return cs.none_schema()
