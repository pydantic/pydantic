"""The annotations handler, splitting the metadata attached to a type between the metadata known by its type handler and the rest."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import Any

from pydantic_core import CoreSchema

from .._constraints import CONSTRAINT_CLASSES
from .._fields import _general_metadata_cls, pydantic_general_metadata


class AnnotationsHandler:
    """Give access to the metadata attached to a type (using `Annotated` or `Field()`) that the type handler knows about.

    The metadata known by a type handler is defined by the `BaseTypeHandler.known_metadata` class variable.
    The remaining metadata (e.g. validators, or any object with a `__get_pydantic_core_schema__()` method) is
    applied by Pydantic *after* the type handler generated the core schema, in the order it was provided.

    As a consequence, the known metadata (e.g. constraints such as `Gt` or `MaxLen`) is applied directly to
    the core schema of the type, regardless of its position relative to the other metadata.
    """

    __slots__ = ('_annotations', '_known_metadata', '_known', '_remaining')

    def __init__(self, annotations: Sequence[Any], known_metadata: frozenset[type[Any]]) -> None:
        self._annotations = annotations
        self._known_metadata = known_metadata
        self._known: list[Any] | None = None
        self._remaining: list[Any] | None = None

    def iter_annotations(self) -> Sequence[Any]:
        """Return the metadata elements known by the type handler, in the order they were provided.

        Metadata classes used without being instantiated (e.g. `Strict` instead of `Strict()`) are instantiated.
        If the same kind of metadata is provided multiple times, all occurrences are returned (meaning the last one
        takes precedence if the type handler applies them in order).
        """
        if self._known is None:
            self._partition()
        return self._known  # pyright: ignore[reportReturnType]

    @property
    def remaining_annotations(self) -> list[Any]:
        """The metadata elements *not* known by the type handler, in the order they were provided."""
        if self._remaining is None:
            self._partition()
        return self._remaining  # pyright: ignore[reportReturnType]

    def _partition(self) -> None:
        known: list[Any] = []
        remaining: list[Any] = []
        known_metadata = self._known_metadata
        general_metadata_cls = _general_metadata_cls()

        for annotation in self._annotations:
            annotation_type = type(annotation)
            if annotation_type in known_metadata:
                known.append(annotation)
            elif annotation_type is type and annotation in known_metadata:
                # Some metadata classes can be used without being instantiated (e.g. `Annotated[int, Strict]`):
                known.append(annotation())
            elif annotation_type is general_metadata_cls:
                # Metadata holding multiple constraints (created by `pydantic_general_metadata()`), split it:
                unknown: dict[str, Any] = {}
                for name, value in annotation.__dict__.items():
                    if value is None:
                        continue
                    constraint_class = CONSTRAINT_CLASSES.get(name)
                    if constraint_class is not None and constraint_class in known_metadata:
                        known.append(constraint_class(value))  # pyright: ignore[reportCallIssue]
                    else:
                        unknown[name] = value
                if unknown:
                    remaining.append(pydantic_general_metadata(**unknown))
            else:
                remaining.append(annotation)

        self._known = known
        self._remaining = remaining


EMPTY_ANNOTATIONS_HANDLER = AnnotationsHandler((), frozenset())
EMPTY_ANNOTATIONS_HANDLER._known = []
EMPTY_ANNOTATIONS_HANDLER._remaining = []


_constraint_keys: dict[type[Any], str] = {}


def _get_constraint_key(metadata_class: type[Any]) -> str:
    try:
        return _constraint_keys[metadata_class]
    except KeyError:
        # The metadata classes holding a single constraint (e.g. `annotated_types.Gt`, `pydantic.Strict`) are
        # dataclasses with a single field, named after the core schema key:
        key = _constraint_keys[metadata_class] = dataclasses.fields(metadata_class)[0].name
        return key


def apply_constraints(schema: CoreSchema, annotations_handler: AnnotationsHandler) -> CoreSchema:
    """Set the constraints known by the type handler on the core schema.

    This assumes each known metadata class is a dataclass holding a single field, named after the core schema key
    (e.g. `annotated_types.Gt` has a `gt` field, matching the `gt` key of the `'int'` core schema).
    """
    known = annotations_handler._known
    if known is None:
        known = annotations_handler.iter_annotations()
    for annotation in known:
        key = _get_constraint_key(type(annotation))
        value = getattr(annotation, key)
        if value is not None:
            schema[key] = value  # pyright: ignore[reportGeneralTypeIssues]
    return schema
