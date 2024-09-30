from __future__ import annotations as _annotations

import functools
import inspect
from functools import partial
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import Any, Awaitable, Callable, Union

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema, _typing_extra
from ._config import ConfigWrapper

# This should be aligned with `GenerateSchema.match_types`
ValidateCallSupportedTypes = Union[
    LambdaType,
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    functools.partial,
]


def get_name(func: ValidateCallSupportedTypes) -> str:
    return f'partial({func.func.__name__})' if isinstance(func, functools.partial) else func.__name__


def get_qualname(func: ValidateCallSupportedTypes) -> str:
    return f'partial({func.func.__qualname__})' if isinstance(func, functools.partial) else func.__qualname__


def _update_wrapper(wrapped: ValidateCallSupportedTypes, wrapper: Callable[..., Any]):
    if inspect.iscoroutinefunction(wrapped):

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

    return wrapper_function


def wrap_validate_call(
    function: ValidateCallSupportedTypes,
    config: ConfigDict | None,
    validate_return: bool,
    namespace: dict[str, Any] | None,
):
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""
    if isinstance(function, partial):
        schema_type = function.func
        module = function.func.__module__
    else:
        schema_type = function
        module = function.__module__
    qualname = core_config_title = get_qualname(function)

    global_ns = _typing_extra.get_module_ns_of(function)
    # TODO: this is a bit of a hack, we should probably have a better way to handle this
    # specifically, we shouldn't be pumping the namespace full of type_params
    # when we take namespace and type_params arguments in eval_type_backport
    type_params = (namespace or {}).get('__type_params__', ()) + getattr(schema_type, '__type_params__', ())
    namespace = {
        **{param.__name__: param for param in type_params},
        **(global_ns or {}),
        **(namespace or {}),
    }
    config_wrapper = ConfigWrapper(config)
    gen_schema = _generate_schema.GenerateSchema(config_wrapper, namespace)
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
        gen_schema = _generate_schema.GenerateSchema(config_wrapper, namespace)
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
        res = function_validator.validate_python(pydantic_core.ArgsKwargs(args, kwargs))
        if return_validator is not None:
            return return_validator(res)
        return res

    wrapper_function = _update_wrapper(function, wrapper)
    wrapper_function.raw_function = function  # type: ignore
    return wrapper_function  # type: ignore
