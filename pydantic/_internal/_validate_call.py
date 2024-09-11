from __future__ import annotations as _annotations

import copy
import inspect
import typing
from functools import lru_cache, partial, wraps
from typing import Any, Awaitable, Callable, TypedDict

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from . import _generate_schema, _generics, _typing_extra
from ._config import ConfigWrapper

if typing.TYPE_CHECKING:
    from typing import TypeGuard

    from ..main import BaseModel
    from ..validate_call_decorator import ValidateCallFunctionType


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
    local_namspace: dict[str, Any] | None


def _is_wrapped_by_validate_call(obj: object) -> TypeGuard[ValidateCallFunctionType]:
    return hasattr(obj, '__pydantic_validate_call_info__')


def collect_validate_call_info(namespace: dict[str, Any]):
    validate_call_infos = {}
    for name, func in namespace.items():
        if _is_wrapped_by_validate_call(func):
            validate_call_infos[name] = func.__pydantic_validate_call_info__

    return validate_call_infos


@lru_cache(maxsize=None)
def _add_unique_postfix(name: str):
    """Used to prevent namespace collision."""
    from uuid import uuid4

    postfix = str(uuid4()).replace('-', '_')
    return f'{name}_{postfix}'


def _replicate_validate_call(function: Callable[..., Any], info: ValidateCallInfo) -> Callable[..., Any]:
    """When normally calling `validate_call`, we use the namespace of the frame that called it as local_ns.
    This function mock that behavior by calling `validate_call` inside a new frame where we have copied all
    local variables into.
    """
    namespace = info['local_namspace']

    locals_name = _add_unique_postfix('locals')
    parent_name = _add_unique_postfix('parent')
    info_name = _add_unique_postfix('info')
    function_name = _add_unique_postfix('function')
    item_name = _add_unique_postfix('item')

    from ..validate_call_decorator import validate_call

    result_ns = {locals_name: namespace, 'validate_call': validate_call, info_name: info, function_name: function}

    exec(
        f"""
def {parent_name}():
    for {item_name} in {locals_name}.items():
        locals()[{item_name}[0]] = {item_name}[1]
    del {item_name}
    return validate_call(config={info_name}['config'], validate_return={info_name}['validate_return'])({function_name})
""",
        result_ns,
    )

    return result_ns[parent_name]()


def _copy_func(function: Callable[..., Any]):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


def update_generic_validate_call_info(model: type[BaseModel]):
    """Called when a generic model is subscripted."""
    origin = model.__pydantic_generic_metadata__['origin']
    typevars_map: dict[Any, Any] | None = _generics.get_model_typevars_map(model)

    if not origin:
        return

    for func_name, info in origin.__pydantic_validate_call_infos__.items():
        info = info.copy()
        function = info['function'] = _copy_func(info['function'])
        function.__annotations__ = copy.copy(function.__annotations__)

        for name, annotation in function.__annotations__.items():
            evaluated_annotation = _typing_extra.eval_type_lenient(
                annotation,
                _typing_extra.get_module_ns_of(origin),
                info['local_namspace'],
            )

            function.__annotations__[name] = _generics.replace_types(evaluated_annotation, typevars_map)

        new_function = _replicate_validate_call(function, info)

        setattr(model, func_name, new_function)
        info['function'] = new_function
        model.__pydantic_validate_call_infos__[func_name] = info
