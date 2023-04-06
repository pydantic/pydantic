from __future__ import annotations as _annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable

import pydantic_core
from typing_extensions import Self

from . import _generate_schema, _typing_extra

if TYPE_CHECKING:
    from ..config import ConfigDict


class ValidateCallWrapper:
    """
    This is a wrapper around a function that validates the arguments passed to it, and optionally the return value.

    It's partially inspired by `wraps` which in turn uses `partial`, but extended to be a descriptor so
    these functions can be applied to instance methods, class methods, static methods, as well as normal functions.
    """

    __slots__ = (
        'raw_function',
        '_config',
        '_validate_return',
        '__pydantic_core_schema__',
        '__pydantic_validator__',
        '__signature__',
        '__name__',
        '__qualname__',
        '__annotations__',
        '__dict__',  # required for __module__
    )

    def __init__(self, function: Callable[..., Any], config: ConfigDict | None, validate_return: bool):
        self.raw_function = function
        self._config = config
        self._validate_return = validate_return
        self.__signature__ = inspect.signature(function)
        self.__name__ = function.__name__
        self.__qualname__ = function.__qualname__
        self.__doc__ = function.__doc__
        self.__annotations__ = function.__annotations__
        self.__module__ = function.__module__

        namespace = _typing_extra.add_module_globals(function, None)
        arbitrary_types_allowed = (config or {}).get('arbitrary_types_allowed', False)
        gen_schema = _generate_schema.GenerateSchema(arbitrary_types_allowed, namespace)
        self.__pydantic_core_schema__ = schema = gen_schema.callable_schema(function, validate_return)
        self.__pydantic_validator__ = pydantic_core.SchemaValidator(schema)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.__pydantic_validator__.validate_python(pydantic_core.ArgsKwargs(args, kwargs))

    def __get__(self, obj: Any, objtype: type[Any] | None = None) -> Self:
        """
        Bind the raw function and return another ValidateCallWrapper wrapping that.
        """
        bound_function = self.raw_function.__get__(obj, objtype)
        return self.__class__(bound_function, self._config, self._validate_return)

    def __repr__(self) -> str:
        return f'ValidateCallWrapper({self.raw_function})'
