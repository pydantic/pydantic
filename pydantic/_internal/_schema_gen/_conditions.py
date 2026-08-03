from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable
from typing import TYPE_CHECKING, Any

import typing_extensions
from typing_extensions import LiteralString

if TYPE_CHECKING:
    from ._type_handlers import BaseTypeHandler
    from ._type_registry import TypeRegistry


class Condition(ABC):
    @abstractmethod
    def register(self, type_registry: TypeRegistry, type_handler_class: type[BaseTypeHandler]) -> None: ...


class TypeIs(Condition):
    def __init__(self, typ: Hashable) -> None:
        self.typ = typ

    def register(self, type_registry: TypeRegistry, type_handler_class: type[BaseTypeHandler]) -> None:
        type_registry.type_is_list[self.typ] = type_handler_class


_unset = object()


class TypeIsTypingMember(Condition):
    def __init__(self, member: LiteralString) -> None:
        self.member = member

    def register(self, type_registry: TypeRegistry, type_handler_class: type[BaseTypeHandler]) -> None:
        for typing_module in (typing, typing_extensions):
            if (typing_member := getattr(typing_module, self.member, _unset)) is not _unset:
                type_registry.type_is_list[typing_member] = type_handler_class


class Predicate(Condition):
    def __init__(self, predicate: Callable[[Any], bool]) -> None:
        self.predicate = predicate

    def register(self, type_registry: TypeRegistry, type_handler_class: type[BaseTypeHandler]) -> None:
        type_registry.predicates[self.predicate] = type_handler_class
