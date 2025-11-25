from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from ._conditions import Condition
    from ._type_handlers import BaseTypeHandler

_TypeHandlerTypeT = TypeVar('_TypeHandlerTypeT', bound='type[BaseTypeHandler]')


class TypeRegistry:
    def __init__(self) -> None:
        self.type_is_list: dict[Any, type[BaseTypeHandler]] = {}
        self.predicates: dict[Callable[[Any], bool], type[BaseTypeHandler]] = {}

    def register(self, condition: Condition) -> Callable[[_TypeHandlerTypeT], _TypeHandlerTypeT]:
        def _inner(type_handler_class: _TypeHandlerTypeT, /) -> _TypeHandlerTypeT:
            condition.register(self, type_handler_class)

            return type_handler_class

        return _inner

    def get_type_handler(self, typ: Any) -> type[BaseTypeHandler] | None:
        try:
            if typ in self.type_is_list:
                return self.type_is_list[typ]
        except TypeError:
            # typ is unhashable
            pass
        for pred, type_handler in self.predicates.items():
            if pred(typ):
                return type_handler
        return None


pydantic_registry = TypeRegistry()
