from __future__ import annotations as _annotations

import functools
import inspect
from functools import partial
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import Any, Awaitable, Callable, Union, get_args

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema
from ._config import ConfigWrapper
from ._namespace_utils import MappingNamespace, NsResolver, ns_for_function

# Note: This does not play very well with type checkers. For example,
# `a: LambdaType = lambda x: x` will raise a type error by Pyright.
ValidateCallSupportedTypes = Union[
    LambdaType,
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    functools.partial,
]

VALIDATE_CALL_SUPPORTED_TYPES = get_args(ValidateCallSupportedTypes)


def get_name(func: ValidateCallSupportedTypes) -> str:
    return f'partial({func.func.__name__})' if isinstance(func, functools.partial) else func.__name__


def get_qualname(func: ValidateCallSupportedTypes) -> str:
    return f'partial({func.func.__qualname__})' if isinstance(func, functools.partial) else func.__qualname__


def update_wrapper(wrapped: ValidateCallSupportedTypes, wrapper: Callable[..., Any]):
    """Update the `wrapper` function with the attributes of the `wrapped` function. Return the updated function."""
    if inspect.iscoroutinefunction(wrapped):
        # We have to create a new couroutine function
        @functools.wraps(wrapped)
        async def wrapper_function(*args, **kwargs):  # type: ignore
            return await wrapper(*args, **kwargs)
    else:

        @functools.wraps(wrapped)
        def wrapper_function(*args, **kwargs):
            return wrapper(*args, **kwargs)

    # We need to manually update this because `partial` object has no `__name__` and `__qualname__`.
    wrapper_function.__name__ = get_name(wrapped)
    wrapper_function.__qualname__ = get_qualname(wrapped)
    wrapper_function.raw_function = wrapped  # type: ignore

    return wrapper_function


class ValidateCallWrapper:
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""

    # This slots are not currently used, but in the future we may want to expose them.
    # See #9883
    __slots__ = (
        '__pydantic_validator__',
        '__name__',
        '__qualname__',
        '__annotations__',
        '__dict__',  # required for __module__
    )

    def __init__(
        self,
        function: ValidateCallSupportedTypes,
        config: ConfigDict | None,
        validate_return: bool,
        parent_namespace: MappingNamespace | None,
    ):
        if isinstance(function, partial):
            schema_type = function.func
            module = function.func.__module__
        else:
            schema_type = function
            module = function.__module__
        qualname = core_config_title = get_qualname(function)

        self.__name__ = get_name(function)
        self.__qualname__ = qualname
        self.__module__ = module

        ns_resolver = NsResolver(namespaces_tuple=ns_for_function(schema_type, parent_namespace=parent_namespace))

        config_wrapper = ConfigWrapper(config)
        gen_schema = _generate_schema.GenerateSchema(config_wrapper, ns_resolver)
        schema = gen_schema.clean_schema(gen_schema.generate_schema(function))
        core_config = config_wrapper.core_config(core_config_title)

        function_validator = create_schema_validator(
            schema,
            schema_type,
            module,
            qualname,
            'validate_call',
            core_config,
            config_wrapper.plugin_settings,
        )

        if validate_return:
            signature = inspect.signature(function)
            return_type = signature.return_annotation if signature.return_annotation is not signature.empty else Any
            gen_schema = _generate_schema.GenerateSchema(config_wrapper, ns_resolver)
            schema = gen_schema.clean_schema(gen_schema.generate_schema(return_type))
            validator = create_schema_validator(
                schema,
                schema_type,
                module,
                qualname,
                'validate_call',
                core_config,
                config_wrapper.plugin_settings,
            )
            if inspect.iscoroutinefunction(function):

                async def return_val_wrapper(aw: Awaitable[Any]) -> None:
                    return validator.validate_python(await aw)

                return_validator = return_val_wrapper
            else:
                return_validator = validator.validate_python
        else:
            return_validator = None

        def wrapper(*args, **kwargs):
            """The wrapper function. Does the same as the original function, but validates the input and output."""
            res = function_validator.validate_python(pydantic_core.ArgsKwargs(args, kwargs))
            if return_validator is not None:
                return return_validator(res)
            return res

        self.__pydantic_validator__ = wrapper

    def __call__(self, *args, **kwargs) -> Any:
        return self.__pydantic_validator__(*args, **kwargs)
