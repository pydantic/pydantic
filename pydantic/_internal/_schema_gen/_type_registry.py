"""The registry of type handlers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from ._type_handlers import BaseTypeHandler

HandlerClassT = TypeVar('HandlerClassT', bound='type[BaseTypeHandler]')


class TypeRegistry:
    """A registry of type handlers.

    Type handlers are registered using their `match_condition`. Handlers registered for an exact type
    are looked up first, then predicates are checked in registration order.
    """

    __slots__ = ('_types', '_predicates')

    def __init__(self) -> None:
        self._types: dict[Any, type[BaseTypeHandler]] = {}
        self._predicates: list[tuple[Callable[[Any], bool], type[BaseTypeHandler]]] = []

    def register(self, handler_class: HandlerClassT, /) -> HandlerClassT:
        """Register a type handler class, using its `match_condition`. Can be used as a decorator."""
        handler_class.match_condition.register(self, handler_class)
        return handler_class

    def register_type(self, tp: Any, handler_class: type[BaseTypeHandler]) -> None:
        self._types[tp] = handler_class

    def register_predicate(self, predicate: Callable[[Any], bool], handler_class: type[BaseTypeHandler]) -> None:
        self._predicates.append((predicate, handler_class))

    def get_exact_handler(self, tp: Any) -> type[BaseTypeHandler] | None:
        """Get the handler class registered for the exact type `tp`."""
        try:
            return self._types.get(tp)
        except TypeError:
            # `tp` is unhashable:
            return None

    def get_predicate_handler(self, tp: Any) -> type[BaseTypeHandler] | None:
        """Get the first handler class whose predicate matches `tp`."""
        for predicate, handler_class in self._predicates:
            if predicate(tp):
                return handler_class
        return None


default_registry = TypeRegistry()
"""The registry holding the type handlers for the types supported by Pydantic.

Handlers are registered when importing the `pydantic._internal._schema_gen._types` package.
"""
