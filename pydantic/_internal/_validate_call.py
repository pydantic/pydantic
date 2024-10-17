from __future__ import annotations as _annotations

import functools
import inspect
import typing
from collections.abc import Mapping
from functools import partial
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import Any, Awaitable, Callable, TypedDict, TypeVar, Union, cast, get_args

import pydantic_core

from ..config import ConfigDict
from ..errors import PydanticUserError
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema, _generics, _typing_extra
from ._config import ConfigWrapper
from ._namespace_utils import MappingNamespace, NsResolver, ns_for_function

if typing.TYPE_CHECKING:
    from ..config import ConfigDict
    from ..main import BaseModel

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


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


_INVALID_TYPE_ERROR_CODE = 'validate-call-type'


def _check_function_type(function: object) -> None:
    """Check if the input function is a supported type for `validate_call`."""
    if isinstance(function, VALIDATE_CALL_SUPPORTED_TYPES):
        try:
            inspect.signature(cast(ValidateCallSupportedTypes, function))
        except ValueError:
            raise PydanticUserError(
                f"Input function `{function}` doesn't have a valid signature", code=_INVALID_TYPE_ERROR_CODE
            )

        if isinstance(function, partial):
            try:
                assert not isinstance(partial.func, partial), 'Partial of partial'
                _check_function_type(function.func)
            except PydanticUserError as e:
                raise PydanticUserError(
                    f'Partial of `{function.func}` is invalid because the type of `{function.func}` is not supported by `validate_call`',
                    code=_INVALID_TYPE_ERROR_CODE,
                ) from e

        return

    if isinstance(function, (classmethod, staticmethod, property)):
        name = type(function).__name__
        raise PydanticUserError(
            f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)',
            code=_INVALID_TYPE_ERROR_CODE,
        )

    if inspect.isclass(function):
        raise PydanticUserError(
            f'Unable to validate {function}: `validate_call` should be applied to functions, not classes (put `@validate_call` on top of `__init__` or `__new__` instead)',
            code=_INVALID_TYPE_ERROR_CODE,
        )
    if callable(function):
        raise PydanticUserError(
            f'Unable to validate {function}: `validate_call` should be applied to functions, not instances or other callables. Use `validate_call` explicitly on `__call__` instead.',
            code=_INVALID_TYPE_ERROR_CODE,
        )

    raise PydanticUserError(
        f'Unable to validate {function}: `validate_call` should be applied to one of the following: function, method, partial, or lambda',
        code=_INVALID_TYPE_ERROR_CODE,
    )


def extract_function_name(func: ValidateCallSupportedTypes) -> str:
    """Extract the name of a `ValidateCallSupportedTypes` object."""
    return f'partial({func.func.__name__})' if isinstance(func, functools.partial) else func.__name__


def extract_function_qualname(func: ValidateCallSupportedTypes) -> str:
    """Extract the qualname of a `ValidateCallSupportedTypes` object."""
    return f'partial({func.func.__qualname__})' if isinstance(func, functools.partial) else func.__qualname__


def update_wrapper_attributes(wrapped: ValidateCallSupportedTypes, wrapper: Callable[..., Any]):
    """Update the `wrapper` function with the attributes of the `wrapped` function. Return the updated function."""
    if inspect.iscoroutinefunction(wrapped):

        @functools.wraps(wrapped)
        async def wrapper_function(*args, **kwargs):  # type: ignore
            return await wrapper(*args, **kwargs)
    else:

        @functools.wraps(wrapped)
        def wrapper_function(*args, **kwargs):
            return wrapper(*args, **kwargs)

    # We need to manually update this because `partial` object has no `__name__` and `__qualname__`.
    wrapper_function.__name__ = extract_function_name(wrapped)
    wrapper_function.__qualname__ = extract_function_qualname(wrapped)
    wrapper_function.raw_function = wrapped  # type: ignore

    return wrapper_function


class ValidateCallWrapper:
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""

    __slots__ = ('__pydantic_validator__', '__return_pydantic_validator__')

    def __init__(
        self,
        function: ValidateCallSupportedTypes,
        config: ConfigDict | None,
        validate_return: bool,
        parent_namespace: MappingNamespace | None,
    ) -> None:
        if isinstance(function, partial):
            schema_type = function.func
            module = function.func.__module__
        else:
            schema_type = function
            module = function.__module__
        qualname = extract_function_qualname(function)

        ns_resolver = NsResolver(namespaces_tuple=ns_for_function(schema_type, parent_namespace=parent_namespace))

        config_wrapper = ConfigWrapper(config)
        gen_schema = _generate_schema.GenerateSchema(config_wrapper, ns_resolver)
        schema = gen_schema.clean_schema(gen_schema.generate_schema(function))
        core_config = config_wrapper.core_config(title=qualname)

        self.__pydantic_validator__ = create_schema_validator(
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

                self.__return_pydantic_validator__ = return_val_wrapper
            else:
                self.__return_pydantic_validator__ = validator.validate_python
        else:
            self.__return_pydantic_validator__ = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        res = self.__pydantic_validator__.validate_python(pydantic_core.ArgsKwargs(args, kwargs))
        if self.__return_pydantic_validator__:
            return self.__return_pydantic_validator__(res)
        else:
            return res


class ValidateCallInfo(TypedDict):
    validate_return: bool
    config: ConfigDict | None
    function: Callable[..., Any]
    local_namespace: dict[str, Any] | None


def validate_call_with_namespace(
    function: AnyCallableT | None = None,
    config: ConfigDict | None = None,
    validate_return: bool = False,
    local_namespace: dict[str, Any] | None = None,
) -> AnyCallableT | Callable[[AnyCallableT], AnyCallableT]:
    def validate(_function: AnyCallableT) -> AnyCallableT:
        _check_function_type(_function)
        function = cast(ValidateCallSupportedTypes, _function)

        validate_call_wrapper = ValidateCallWrapper(
            cast(ValidateCallSupportedTypes, function), config, validate_return, local_namespace
        )

        wrapper_function = update_wrapper_attributes(function, validate_call_wrapper.__call__)

        info = ValidateCallInfo(
            validate_return=validate_return,
            config=config,
            function=function,
            local_namespace=local_namespace,
        )
        wrapper_function.__pydantic_validate_call_info__ = info  # type: ignore

        return cast(Any, wrapper_function)

    if function is not None:
        return validate(function)
    else:
        return validate


def _is_wrapped_by_validate_call(obj: object) -> bool:
    return hasattr(obj, '__pydantic_validate_call_info__')


def collect_validate_call_info(namespace: Mapping[str, Any]) -> dict[str, ValidateCallInfo]:
    return {
        name: func.__pydantic_validate_call_info__
        for name, func in namespace.items()
        if _is_wrapped_by_validate_call(func)
    }


def _update_qualname(function: Callable[..., Any], model: type[BaseModel]) -> None:
    origin = model.__pydantic_generic_metadata__['origin']
    if not origin:
        return

    name = function.__name__
    qualname = function.__qualname__

    original_postfix = f'{origin.__name__}.{name}'
    assert qualname.endswith(original_postfix)
    function.__qualname__ = qualname.replace(original_postfix, f'{model.__name__}.{name}')


def update_generic_validate_calls(model: type[BaseModel]) -> None:
    """Recreate the methods decorated with `validate_call`, replacing any parametrized class scoped type variables."""
    origin = model.__pydantic_generic_metadata__['origin']
    typevars_map = _generics.get_model_typevars_map(model)

    if not origin:
        return

    updated_funcs: dict[str, Any] = {}
    for func_name, info in origin.__pydantic_validate_calls__.items():
        info = info.copy()
        function = info['function']

        # we want to temporarily reassign the annotations to generate schema
        original_annotations = function.__annotations__
        original_qualname = function.__qualname__
        original_signature = inspect.signature(function)

        function.__annotations__ = original_annotations.copy()
        function.__dict__.pop('__signature__', None)
        _update_qualname(function, model)

        for name, annotation in function.__annotations__.items():
            evaluated_annotation = _typing_extra.eval_type_lenient(
                annotation,
                _typing_extra.get_module_ns_of(origin),
                info['local_namespace'],
            )

            function.__annotations__[name] = _generics.replace_types(evaluated_annotation, typevars_map)

        # Note: `__signature__` of raw function will be updated, so we need to reset it later
        new_function = validate_call_with_namespace(**info)
        new_function.__signature__ = inspect.signature(function)  # type: ignore

        function.__annotations__ = original_annotations
        function.__qualname__ = original_qualname
        function.__signature__ = original_signature  # type: ignore

        setattr(model, func_name, new_function)
        updated_funcs[func_name] = new_function

    model.__pydantic_validate_calls__ = collect_validate_call_info(updated_funcs)
