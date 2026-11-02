"""Constraint metadata classes, created from `Field()` arguments, `StringConstraints` and `condecimal()`.

Each class holds a single constraint, named after the corresponding core schema key. This allows type handlers
to declare exactly which constraints they support (see `BaseTypeHandler.known_metadata`).

These replace the `_PydanticGeneralMetadata` class, that was holding several unrelated constraints.
"""

from __future__ import annotations

import dataclasses
from re import Pattern as RePattern
from typing import Any, Literal

from ._fields import PydanticMetadata


@dataclasses.dataclass(frozen=True)
class Pattern(PydanticMetadata):
    """The string should match the regular expression."""

    pattern: str | RePattern[str]


@dataclasses.dataclass(frozen=True)
class StripWhitespace(PydanticMetadata):
    """Whether to strip leading and trailing whitespace from the string."""

    strip_whitespace: bool


@dataclasses.dataclass(frozen=True)
class ToLower(PydanticMetadata):
    """Whether to convert the string to lowercase."""

    to_lower: bool


@dataclasses.dataclass(frozen=True)
class ToUpper(PydanticMetadata):
    """Whether to convert the string to uppercase."""

    to_upper: bool


@dataclasses.dataclass(frozen=True)
class AsciiOnly(PydanticMetadata):
    """Whether the string should only contain ASCII characters."""

    ascii_only: bool


@dataclasses.dataclass(frozen=True)
class CoerceNumbersToStr(PydanticMetadata):
    """Whether to coerce numbers to strings."""

    coerce_numbers_to_str: bool


@dataclasses.dataclass(frozen=True)
class MaxDigits(PydanticMetadata):
    """The maximum number of digits of a decimal."""

    max_digits: int


@dataclasses.dataclass(frozen=True)
class DecimalPlaces(PydanticMetadata):
    """The maximum number of decimal places of a decimal."""

    decimal_places: int


@dataclasses.dataclass(frozen=True)
class UnionMode(PydanticMetadata):
    """The validation mode of a union."""

    union_mode: Literal['smart', 'left_to_right']


CONSTRAINT_CLASSES: dict[str, type[PydanticMetadata]] = {
    'pattern': Pattern,
    'strip_whitespace': StripWhitespace,
    'to_lower': ToLower,
    'to_upper': ToUpper,
    'ascii_only': AsciiOnly,
    'coerce_numbers_to_str': CoerceNumbersToStr,
    'max_digits': MaxDigits,
    'decimal_places': DecimalPlaces,
    'union_mode': UnionMode,
}
"""A mapping between constraint names and the class holding the constraint."""


def constraints_from_kwargs(**kwargs: Any) -> list[PydanticMetadata]:
    """Create the constraint metadata instances from the provided keyword arguments, skipping `None` values."""
    return [CONSTRAINT_CLASSES[k](v) for k, v in kwargs.items() if v is not None]  # pyright: ignore[reportCallIssue]
