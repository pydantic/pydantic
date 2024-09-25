from __future__ import annotations as _annotations

import inspect
from functools import partial
from types import FunctionType, LambdaType, MethodType
from typing import Any, Awaitable, Callable

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema, _typing_extra
from ._config import ConfigWrapper

_validate_call_handle_types: tuple[type[Any], ...] = (
    FunctionType,
    LambdaType,
    MethodType,
    partial,
)


def _check_function_type(function: object):
    if any(isinstance(function, t) for t in _validate_call_handle_types):
        return

    if isinstance(function, (classmethod, staticmethod)):
        name = type(function).__name__
        raise TypeError(f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)')

    if inspect.isclass(function):
        raise TypeError(
            '`validate_call` should be applied to functions, not classes (put `@validate_call` on top of `__init__` or `__new__` instead)'
        )
    if callable(function):
        raise TypeError(
            '`validate_call` should be applied to functions, not instances or other callables. Use `validate_call` explicitly on `__call__` instead.'
        )

    raise TypeError('`validate_call` should be applied to one of the following: function, method, partial, or lambda')


def wrap_validate_call(
    function: Callable[..., Any],
    config: ConfigDict | None,
    validate_return: bool,
    namespace: dict[str, Any] | None,
):
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""
    _check_function_type(function)

    if isinstance(function, partial):
        schema_type = function.func
        module = function.func.__module__
        qualname = f'partial({function.func.__qualname__})'
        core_config_title = f'partial({function.func.__name__})'
    else:
        schema_type = function
        module = function.__module__
        qualname = function.__qualname__
        core_config_title = function.__name__

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

    return wrapper
