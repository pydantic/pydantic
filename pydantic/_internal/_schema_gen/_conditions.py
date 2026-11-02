"""Conditions used to determine which type handler should be used for a type."""

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import typing_extensions

if TYPE_CHECKING:
    from ._type_handlers import BaseTypeHandler
    from ._type_registry import TypeRegistry


class Condition(ABC):
    """A condition determining whether a type handler should be used for a type.

    Conditions are matched against the type itself if unparameterized, or against its origin
    if parameterized (e.g. `list` for both `list` and `list[int]`).
    """

    @abstractmethod
    def register(self, registry: TypeRegistry, handler_class: type[BaseTypeHandler]) -> None:
        """Register `handler_class` in `registry`, using this condition."""

    def __or__(self, other: Condition) -> Condition:
        return AnyOf(self, other)


class TypeIs(Condition):
    """Match one or more types by identity.

    This condition is checked first (and is the most efficient one).
    """

    def __init__(self, *types: Any) -> None:
        self.types = types

    def register(self, registry: TypeRegistry, handler_class: type[BaseTypeHandler]) -> None:
        for tp in self.types:
            registry.register_type(tp, handler_class)


_unset = object()


class TypeIsTypingMember(Condition):
    """Match the member named `name` of the `typing` and `typing_extensions` modules (e.g. `'Any'`)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def register(self, registry: TypeRegistry, handler_class: type[BaseTypeHandler]) -> None:
        for module in (typing, typing_extensions):
            if (member := getattr(module, self.name, _unset)) is not _unset:
                registry.register_type(member, handler_class)


class Predicate(Condition):
    """Match types satisfying the predicate.

    Predicates are checked in registration order, after `TypeIs` conditions.
    """

    def __init__(self, predicate: Callable[[Any], bool]) -> None:
        self.predicate = predicate

    def register(self, registry: TypeRegistry, handler_class: type[BaseTypeHandler]) -> None:
        registry.register_predicate(self.predicate, handler_class)


class AnyOf(Condition):
    """Match if any of the conditions matches."""

    def __init__(self, *conditions: Condition) -> None:
        self.conditions = conditions

    def register(self, registry: TypeRegistry, handler_class: type[BaseTypeHandler]) -> None:
        for condition in self.conditions:
            condition.register(registry, handler_class)

    def __or__(self, other: Condition) -> Condition:
        return AnyOf(*self.conditions, other)
