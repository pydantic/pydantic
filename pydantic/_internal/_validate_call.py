from __future__ import annotations as _annotations

import inspect
from dataclasses import dataclass
from functools import partial
from typing import Any, Awaitable, Callable

import pydantic_core

from ..config import ConfigDict
from . import _discriminated_union, _generate_schema, _typing_extra
from ._config import ConfigWrapper
from ._core_utils import flatten_schema_defs, inline_schema_defs


@dataclass
class CallMarker:
    function: Callable[..., Any]
    validate_return: bool


class ValidateCallWrapper:
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value.

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
        if isinstance(function, partial):
            func = function.func
            self.__name__ = f'partial({func.__name__})'
            self.__qualname__ = f'partial({func.__qualname__})'
            self.__annotations__ = func.__annotations__
            self.__module__ = func.__module__
            self.__doc__ = func.__doc__
        else:
            self.__name__ = function.__name__
            self.__qualname__ = function.__qualname__
            self.__annotations__ = function.__annotations__
            self.__module__ = function.__module__
            self.__doc__ = function.__doc__

        namespace = _typing_extra.add_module_globals(function, None)
        config_wrapper = ConfigWrapper(config)
        gen_schema = _generate_schema.GenerateSchema(config_wrapper, namespace)
        self.__pydantic_core_schema__ = schema = gen_schema.collect_definitions(gen_schema.generate_schema(function))
        core_config = config_wrapper.core_config(self)
        schema = _discriminated_union.apply_discriminators(flatten_schema_defs(schema))
        simplified_schema = inline_schema_defs(schema)
        self.__pydantic_validator__ = pydantic_core.SchemaValidator(simplified_schema, core_config)

        if self._validate_return:
            return_type = (
                self.__signature__.return_annotation
                if self.__signature__.return_annotation is not self.__signature__.empty
                else Any
            )
            gen_schema = _generate_schema.GenerateSchema(config_wrapper, namespace)
            self.__return_pydantic_core_schema__ = schema = gen_schema.collect_definitions(
                gen_schema.generate_schema(return_type)
            )
            core_config = config_wrapper.core_config(self)
            schema = _discriminated_union.apply_discriminators(flatten_schema_defs(schema))
            simplified_schema = inline_schema_defs(schema)
            validator = pydantic_core.SchemaValidator(simplified_schema, core_config)
            if inspect.iscoroutinefunction(self.raw_function):

                async def return_val_wrapper(aw: Awaitable[Any]) -> None:
                    return validator.validate_python(await aw)

                self.__return_pydantic_validator__ = return_val_wrapper
            else:
                self.__return_pydantic_validator__ = validator.validate_python
        else:
            self.__return_pydantic_core_schema__ = None
            self.__return_pydantic_validator__ = None

        self._name: str | None = None  # set by __get__, used to set the instance attribute when decorating methods

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        res = self.__pydantic_validator__.validate_python(pydantic_core.ArgsKwargs(args, kwargs))
        if self.__return_pydantic_validator__:
            return self.__return_pydantic_validator__(res)
        return res

    def __get__(self, obj: Any, objtype: type[Any] | None = None) -> BoundValidateCallWrapper:
        """Bind the raw function and return another ValidateCallWrapper wrapping that."""
        if obj is None:
            return BoundValidateCallWrapper(self, objtype)

        return BoundValidateCallWrapper(self, obj)

    def __set_name__(self, owner: Any, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return f'ValidateCallWrapper({self.raw_function})'


class BoundValidateCallWrapper:
    """This class controls the binding logic for a validate call wrapper.

    Allows us to avoid using __setattr__ and mutating the obj.
    """

    def __init__(self, unbound: ValidateCallWrapper, obj: Any) -> None:
        self.unbound = unbound
        self.obj = obj

    def __call__(self, *args, **kwargs) -> Any:
        return self.unbound(self.obj, *args, *kwargs)

    def __eq__(self, other) -> bool:
        if isinstance(other, BoundValidateCallWrapper):
            return (self.unbound == other.unbound) and (self.obj == other.obj)
        else:
            return False
