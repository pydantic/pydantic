from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from pydantic_core.core_schema import CoreSchema
from typing_extensions import TypedDict, get_args


if TYPE_CHECKING:
    from .._generate_schema import GenerateSchema


class BaseTypeHandler(ABC):
    known_metadata: ClassVar[set[type[Any]]] = set()  # Default?

    def __init__(self, generate_schema: GenerateSchema) -> None:
        self.generate_schema = generate_schema

    @abstractmethod
    def _generate_schema(self, origin, obj) -> CoreSchema:
        pass

    # TODO: classmethod?
    def get_reference(self, origin, obj) -> str | None:
        return None


class TypeHandler(BaseTypeHandler, ABC):
    def _generate_schema(self, origin, obj) -> CoreSchema:
        return self.handle_type(obj)

    @abstractmethod
    def handle_type(self, type: Any) -> CoreSchema:
        pass


class GenericTypeHandler(BaseTypeHandler, ABC):
    # is_user_defined: ClassVar[bool] = True
    # """Whether the generic type was user-defined.

    # A [user-defined](https://docs.python.org/3/library/typing.html#user-defined-generics) type is a class
    # that inherits from `typing.Generic` (either explicitly or using the PEP 695 syntax).

    # A generic type that is *not* user-defined is either a built-in type (such as `list`) or a type from
    # the standard library (such as `collections.abc.Container`). These types don't inherit from `Generic`,
    # and instead provide a simple `__class_getitem__` implementation that does not check the provided number
    # of type arguments.

    # For this reason, if the handled type is *not* user-defined, the type handler class must define the number
    # of expected type parameters (e.g. for `list`, `number_of_parameters` should be set to `1`).
    # """

    # number_of_parameters: ClassVar[int]
    # """The number of parameters for the generic type, if *not* user-defined."""

    # def __init_subclass__(cls) -> None:
    #     if not cls.is_user_defined and not hasattr(cls, 'number_of_parameters'):
    #         raise TypeError(f'Type handler {cls.__qualname__!r} is defined to handle bui')

    def _get_parameters(self, obj: Any) -> tuple[Any, ...]:
        return obj.__parameters__

    def _generate_schema(self, origin: Any, obj: Any) -> CoreSchema:
        if origin is None:
            return self.handle_type(obj, self._get_parameters(obj))
        else:
            return self.handle_type(origin, get_args(obj))

    @abstractmethod
    def handle_type(self, type: Any, args: tuple[Any, ...]) -> CoreSchema:
        pass


class StdlibGenericTypeHandler(GenericTypeHandler, ABC):
    parameters: ClassVar[tuple[Any, ...]] = ()

    def _get_parameters(self, obj: Any) -> tuple[Any, ...]:
        return self.parameters

