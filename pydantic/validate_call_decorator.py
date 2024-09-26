"""Decorator for validating function calls."""

from __future__ import annotations as _annotations

import functools
import inspect
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

from ._internal import _typing_extra, _validate_call

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])

# This should be aligned with `GenerateSchema.match_types`
_validate_call_supported_types: tuple[type[Any], ...] = (
    LambdaType,
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    functools.partial,
)


def _check_function_type(function: object):
    if any(isinstance(function, t) for t in _validate_call_supported_types):
        try:
            assert callable(function)  # for type checking
            inspect.signature(function)
        except ValueError:
            # partial doesn't have a qualname, so we just not include it in the error message
            maybe_qualname = f'`{function.__qualname__}` ' if hasattr(function, '__qualname__') else ''
            raise TypeError(f"Input function {maybe_qualname}doesn't have a valid signature")
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


@overload
def validate_call(
    *, config: ConfigDict | None = None, validate_return: bool = False
) -> Callable[[AnyCallableT], AnyCallableT]: ...


@overload
def validate_call(func: AnyCallableT, /) -> AnyCallableT: ...


def validate_call(
    func: AnyCallableT | None = None,
    /,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]:
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/validation_decorator/

    Returns a decorated wrapper around the function that validates the arguments and, optionally, the return value.

    Usage may be either as a plain decorator `@validate_call` or with arguments `@validate_call(...)`.

    Args:
        func: The function to be decorated.
        config: The configuration dictionary.
        validate_return: Whether to validate the return value.

    Returns:
        The decorated function.
    """
    local_ns = _typing_extra.parent_frame_namespace()

    def validate(function: AnyCallableT) -> AnyCallableT:
        _check_function_type(function)

        validate_call_wrapper = _validate_call.wrap_validate_call(function, config, validate_return, local_ns)
        return validate_call_wrapper  # type: ignore

    if func:
        return validate(func)
    else:
        return validate
