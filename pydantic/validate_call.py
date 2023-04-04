from __future__ import annotations as _annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeVar, overload

import pydantic_core
from typing_extensions import ParamSpec

from ._internal import _generate_schema, _typing_extra

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
        namespace = _typing_extra.add_module_globals(function, None)
        arbitrary_types_allowed = (config or {}).get('arbitrary_types_allowed', False)
        gen_schema = _generate_schema.GenerateSchema(arbitrary_types_allowed, namespace)
        schema = gen_schema.callable_schema(function, validate_return)
        validator = pydantic_core.SchemaValidator(schema)
        ArgsKwargs = pydantic_core.ArgsKwargs

        @wraps(function)
        def wrapper_function(*args: Params.args, **kwargs: Params.kwargs) -> ReturnType:
            return validator.validate_python(ArgsKwargs(args, kwargs))

        wrapper_function.raw_function = function  # type: ignore[attr-defined]
        wrapper_function.__pydantic_core_schema__ = schema  # type: ignore[attr-defined]
        wrapper_function.__pydantic_validator__ = validator  # type: ignore[attr-defined]
        return wrapper_function

    if __func:
        return validate(__func)
    else:
        return validate
