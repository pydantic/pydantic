from __future__ import annotations as _annotations

import inspect
import typing
from functools import partial, wraps
from typing import Any, Awaitable, Callable, TypedDict, TypeVar

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema, _generics, _typing_extra
from ._config import ConfigWrapper

if typing.TYPE_CHECKING:
    from ..config import ConfigDict
    from ..main import BaseModel

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


class ValidateCallWrapper:
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""

    __slots__ = (
        '__pydantic_validator__',
        '__name__',
        '__qualname__',
        '__annotations__',
        '__dict__',  # required for __module__
    )

    def __init__(
        self,
        function: Callable[..., Any],
        config: ConfigDict | None,
        validate_return: bool,
        namespace: dict[str, Any] | None,
    ):
        if isinstance(function, partial):
            func = function.func
            schema_type = func
            self.__name__ = f'partial({func.__name__})'
            self.__qualname__ = f'partial({func.__qualname__})'
            self.__module__ = func.__module__
        else:
            schema_type = function
            self.__name__ = function.__name__
            self.__qualname__ = function.__qualname__
            self.__module__ = function.__module__

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
        core_config = config_wrapper.core_config(self)

        self.__pydantic_validator__ = create_schema_validator(
            schema,
            schema_type,
            self.__module__,
            self.__qualname__,
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
                self.__module__,
                self.__qualname__,
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
    def validate(function: AnyCallableT) -> AnyCallableT:
        if isinstance(function, (classmethod, staticmethod)):
            name = type(function).__name__
            raise TypeError(f'The `@{name}` decorator should be applied after `@validate_call` (put `@{name}` on top)')

        validate_call_wrapper = ValidateCallWrapper(function, config, validate_return, local_namespace)

        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def wrapper_function(*args, **kwargs):  # type: ignore
                return await validate_call_wrapper(*args, **kwargs)
        else:

            @wraps(function)
            def wrapper_function(*args, **kwargs):
                return validate_call_wrapper(*args, **kwargs)

        wrapper_function.raw_function = function  # type: ignore

        info = ValidateCallInfo(
            validate_return=validate_return,
            config=config,
            function=function,
            local_namespace=local_namespace,
        )
        wrapper_function.__pydantic_validate_call_info__ = info  # type: ignore

        return wrapper_function  # type: ignore

    if function:
        return validate(function)
    else:
        return validate


def _is_wrapped_by_validate_call(obj: object) -> bool:
    return hasattr(obj, '__pydantic_validate_call_info__')


def collect_validate_call_info(namespace: dict[str, Any]) -> dict[str, ValidateCallInfo]:
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

    for func_name, info in origin.__pydantic_validate_calls__.items():
        info = info.copy()
        function = info['function']

        # we want to temporarily reassign the annotations to generate schema
        original_annotations = function.__annotations__
        original_qualname = function.__qualname__
        original_signature = inspect.signature(function)

        _update_qualname(function, model)
        function.__annotations__ = original_annotations.copy()
        function.__dict__.pop('__signature__', None)

        for name, annotation in function.__annotations__.items():
            evaluated_annotation = _typing_extra.eval_type_lenient(
                annotation,
                _typing_extra.get_module_ns_of(origin),
                info['local_namespace'],
            )

            function.__annotations__[name] = _generics.replace_types(evaluated_annotation, typevars_map)

        # Note: `__signature__` of raw function will be updated too, so we need to update it back
        new_function = validate_call_with_namespace(**info)
        new_function.__signature__ = inspect.signature(function)  # type: ignore

        function.__annotations__ = original_annotations
        function.__qualname__ = original_qualname
        function.__signature__ = original_signature  # type: ignore

        setattr(model, func_name, new_function)
        model.__pydantic_validate_calls__[func_name] = info
