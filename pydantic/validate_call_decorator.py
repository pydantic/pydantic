"""Decorator for validating function calls."""

from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

from ._internal import _typing_extra, _validate_call

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


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
    if (local_ns := _typing_extra.parent_frame_namespace()) and '__type_params__' in local_ns:
        # When using PEP 695 syntax, an extra frame is created, which stores the type parameters.
        # So the `local_ns` above does not contain the TypeVar.
        #
        # Note: since Python 3.13, `typing._eval_type` starts accepting `type_params`;
        #       but that way won't work for Python 3.12 (which PEP 695 is introduced in).

        generic_param_ns = _typing_extra.parent_frame_namespace(parent_depth=3) or {}
        local_ns = {**generic_param_ns, **local_ns}

    return _validate_call.validate_call_with_namespace(func, config, validate_return, local_ns)
