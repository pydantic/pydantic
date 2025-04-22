"""Type handlers for (non-generic) standard library types, such as `datetime.date`, `decimal.Decimal`, etc."""

from __future__ import annotations

import datetime
import ipaddress
import pathlib
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID
from zoneinfo import ZoneInfo

import annotated_types as at
import pydantic_core.core_schema as cs
from pydantic_core import CoreSchema
from typing_inspection import typing_objects

from pydantic import Strict

from .._conditions import Predicate, TypeIs
from .._type_handlers import TypeHandler
from .._type_registry import pydantic_registry

if TYPE_CHECKING:
    from .._annotations_handler import AnnotationsHandler


@pydantic_registry.register(condition=TypeIs(datetime.date))
class DateTypeHandler(TypeHandler):
    """Type handler for standard library type `datetime.date`."""

    # TODO: Annotations such as `PastDate` should be handled here
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.date_schema()
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


@pydantic_registry.register(condition=TypeIs(datetime.datetime))
class DatetimeTypeHandler(TypeHandler):
    """Type handler for standard library type `datetime.datetime`."""

    # TODO: Annotations such as `PastDatetime` should be handled here
    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.datetime_schema()
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


@pydantic_registry.register(condition=TypeIs(datetime.time))
class TimeTypeHandler(TypeHandler):
    """Type handler for standard library type `datetime.time`."""

    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.time_schema()
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


@pydantic_registry.register(condition=TypeIs(datetime.timedelta))
class TimedeltaTypeHandler(TypeHandler):
    """Type handler for standard library type `datetime.timedelta`."""

    known_metadata = {at.Gt, at.Ge, at.Lt, at.Le, Strict}

    def handle_type(self, type: type[int], annotations_handler: AnnotationsHandler) -> CoreSchema:
        schema = cs.timedelta_schema()
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


@pydantic_registry.register(condition=Predicate(typing_objects.is_typevar))
class TypeVarTypeHandler(TypeHandler):
    known_metadata = set()

    def handle_type(self, type: TypeVar, annotations_handler: AnnotationsHandler) -> CoreSchema:
        typevar = type
        try:
            has_default = typevar.has_default()
        except AttributeError:
            # Happens if using `typing.TypeVar` (and not `typing_extensions`) on Python < 3.13
            pass
        else:
            if has_default:
                return self.generate_schema.generate_schema(typevar.__default__)

        if constraints := typevar.__constraints__:
            return self.generate_schema.generate_schema(typing.Union[constraints])

        if bound := typevar.__bound__:
            schema = self.generate_schema.generate_schema(bound)
            schema['serialization'] = cs.wrap_serializer_function_ser_schema(
                lambda x, h: h(x),
                schema=cs.any_schema(),
            )
            return schema

        return cs.any_schema()


# Temp handlers:
import collections.abc
import typing

from pydantic_core import MultiHostUrl, Url


@pydantic_registry.register(condition=TypeIs(Decimal))
@pydantic_registry.register(condition=TypeIs(UUID))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv4Address))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv4Interface))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv4Network))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv6Address))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv6Interface))
@pydantic_registry.register(condition=TypeIs(ipaddress.IPv6Network))
@pydantic_registry.register(condition=TypeIs(pathlib.Path))
@pydantic_registry.register(condition=TypeIs(pathlib.PurePath))
@pydantic_registry.register(condition=TypeIs(pathlib.PosixPath))
@pydantic_registry.register(condition=TypeIs(pathlib.PurePosixPath))
@pydantic_registry.register(condition=TypeIs(pathlib.PureWindowsPath))
@pydantic_registry.register(condition=TypeIs(ZoneInfo))
# Should be in another module:
@pydantic_registry.register(condition=TypeIs(Fraction))
@pydantic_registry.register(condition=TypeIs(Url))
@pydantic_registry.register(condition=TypeIs(MultiHostUrl))
@pydantic_registry.register(condition=TypeIs(collections.abc.Hashable))
class PlaceholderTypeHandler(TypeHandler):
    """Placeholder handler."""

    known_metadata = set()

    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        raise NotImplementedError
