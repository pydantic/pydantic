from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Callable, TypeVar, overload

from typing_extensions import ParamSpec

from ._internal import _validate_call

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    Params = ParamSpec('Params')
    ReturnType = TypeVar('ReturnType')


@overload
def validate_call(
    *, config: ConfigDict | None = None, validate_return: bool = False
) -> Callable[[Callable[Params, ReturnType]], Callable[Params, ReturnType]]:
    ...


@overload
def validate_call(__func: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
    ...


def validate_call(
    __func: Callable[Params, ReturnType] | None = None,
    *,
    config: ConfigDict | None = None,
    validate_return: bool = False,
) -> Callable[Params, ReturnType] | Callable[[Callable[Params, ReturnType]], Callable[Params, ReturnType]]:
    """
    Decorator to validate the arguments passed to a function, and optionally the return value.
    """

    def validate(function: Callable[Params, ReturnType]) -> Callable[Params, ReturnType]:
        return _validate_call.ValidateCallWrapper(function, config, validate_return)  # type: ignore

    if __func:
        return validate(__func)
    else:
        return validate
