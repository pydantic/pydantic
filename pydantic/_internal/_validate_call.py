from __future__ import annotations as _annotations

import functools
import inspect
from functools import partial
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, LambdaType, MethodType
from typing import Any, Awaitable, Callable, Union, cast, get_args

from pydantic_core import ArgsKwargs, SchemaValidator
from typing_extensions import ParamSpec, TypeVar, TypeVarTuple

from ..config import ConfigDict
from ..plugin._schema_validator import PluggableSchemaValidator, create_schema_validator
from . import _generate_schema
from ._config import ConfigWrapper
from ._namespace_utils import MappingNamespace, NsResolver, ns_for_function


def extract_function_name(func: ValidateCallSupportedTypes) -> str:
    """Extract the name of a `ValidateCallSupportedTypes` object."""
    return f'partial({func.func.__name__})' if isinstance(func, functools.partial) else func.__name__


def extract_function_qualname(func: ValidateCallSupportedTypes) -> str:
    """Extract the qualname of a `ValidateCallSupportedTypes` object."""
    return f'partial({func.func.__qualname__})' if isinstance(func, functools.partial) else func.__qualname__


class ValidateCallWrapper:
    """This is a wrapper around a function that validates the arguments passed to it, and optionally the return value."""

    __slots__ = (
        #
        # Below are attributes similar to `wraps`.
        # The commented out attributes may conflict with the class variables;
        # so they are actually stored in `__dict__` at instance level.
        #
        # '__module__',
        '__name__',
        '__qualname__',
        # '__doc__',
        # '__annotations__',
        '__type_params__',
        '__dict__',
        #
        '__pydantic_validator__',
        '__return_pydantic_validator__',
        #
        'raw_function',
        'config',
        'validate_return',
        'parent_namespace',
    )

    __module__: str
    __name__: str
    __qualname__: str
    __doc__: str | None
    # # TODO: test this
    __annotations__: dict[str, type]
    # # TODO: test this
    __type_params__: tuple[TypeVar | ParamSpec | TypeVarTuple, ...] | None

    __pydantic_validator__: SchemaValidator | PluggableSchemaValidator
    __return_pydantic_validator__: Callable[[Any], Any] | None

    raw_function: ValidateCallSupportedTypes
    config: ConfigDict | None
    validate_return: bool
    parent_namespace: MappingNamespace | None
    _repr_dummy: Callable

    _name: str | None = None
    _owner: type[Any] | None = None

    def __init__(
        self,
        function: ValidateCallSupportedTypes,
        config: ConfigDict | None,
        validate_return: bool,
        parent_namespace: MappingNamespace | None,
    ) -> None:
        if isinstance(function, partial):
            schema_type = function.func
            wrapped = function.func
        else:
            schema_type = function
            wrapped = function

        module = wrapped.__module__
        function_name = extract_function_name(function)
        qualname = extract_function_qualname(function)

        # `functools.wraps` do most of the work here except for `__name__` and `__qualname__`.
        functools.wraps(wrapped)(self)
        self.__name__ = function_name
        self.__qualname__ = qualname

        self.raw_function = function
        self.config = config
        self.validate_return = validate_return
        self.parent_namespace = parent_namespace

        self._repr_dummy = functools.wraps(self)(lambda: ...)

        if inspect.iscoroutinefunction(function):
            inspect.markcoroutinefunction(self)

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
        res = self.__pydantic_validator__.validate_python(ArgsKwargs(args, kwargs))
        if self.__return_pydantic_validator__:
            return self.__return_pydantic_validator__(res)
        else:
            return res

    def __get__(self, obj: Any, objtype: type[Any] | None = None) -> ValidateCallWrapper:
        """Bind the raw function and return another ValidateCallWrapper wrapping that."""
        objtype = objtype or cast(type, obj.__class__)
        if obj is None:
            # It's possible this wrapper is dynamically applied to a class attribute not allowing
            # name to be populated by __set_name__. In this case, we'll manually acquire the name
            # from the function reference.
            if self._name is None:
                self._name = extract_function_name(self.raw_function)
            try:
                # Handle the case where a method is accessed as a class attribute
                return objtype.__getattribute__(objtype, self._name)  # type: ignore
            except AttributeError:
                # This will happen the first time the attribute is accessed
                pass

        bound_func = cast(Callable, self.raw_function).__get__(obj, objtype)
        validated_func = self.__class__(bound_func, self.config, self.validate_return, self.parent_namespace)

        # skip binding to instance when obj or objtype has __slots__ attribute
        slots = getattr(obj, '__slots__', getattr(objtype, '__slots__', None))
        # if hasattr(obj, '__slots__') or hasattr(objtype, '__slots__'):
        if slots is not None and self._name not in slots:
            return validated_func

        if self._name is not None:
            if obj is None:
                object.__setattr__(objtype, self._name, validated_func)
            elif objtype is self._owner:
                object.__setattr__(obj, self._name, validated_func)
        return validated_func

    def __set_name__(self, owner: Any, name: str) -> None:
        # TODO: handle more the case this is not called
        self._owner = owner
        self._name = name

    def __repr__(self) -> str:
        # TODO: test this
        # return f'ValidateCallWrapper({self.raw_function})'
        return repr(self._repr_dummy)

    def __eq__(self, value: object) -> bool:
        # TODO: test this
        if isinstance(value, ValidateCallWrapper):
            return self.raw_function == value.raw_function
        return False

    def __hash__(self):
        # TODO: test this
        return hash(self.raw_function)


# Note: This does not play very well with type checkers. For example,
# `a: LambdaType = lambda x: x` will raise a type error by Pyright.
ValidateCallSupportedTypes = Union[
    LambdaType,
    FunctionType,
    MethodType,
    BuiltinFunctionType,
    BuiltinMethodType,
    functools.partial,
    ValidateCallWrapper,
]

VALIDATE_CALL_SUPPORTED_TYPES = get_args(ValidateCallSupportedTypes)
