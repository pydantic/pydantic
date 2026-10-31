from __future__ import annotations as _annotations

import collections.abc
import functools
import inspect
from collections.abc import Awaitable, Callable
from functools import partial
from typing import Any

import pydantic_core

from ..config import ConfigDict
from ..plugin._schema_validator import create_schema_validator
from ._config import ConfigWrapper
from ._generate_schema import GenerateSchema, ValidateCallSupportedTypes
from ._namespace_utils import MappingNamespace, NsResolver, ns_for_function
from ._typing_extra import signature_no_eval


class _IdempotentIterable(collections.abc.Iterator):
    """A wrapper around one-shot iterators/generators that preserves read elements,
    preventing earlier candidate union branches in validate_call from draining
    the iterable before an Iterable branch is evaluated.
    """

    __slots__ = ('_iterable', '_cached', '_exhausted', '_next_index')

    def __init__(self, iterable: collections.abc.Iterable[Any]) -> None:
        self._iterable = iter(iterable)
        self._cached: list[Any] = []
        self._exhausted = False
        self._next_index = 0

    def __iter__(self) -> collections.abc.Iterator[Any]:
        index = 0
        while True:
            if index < len(self._cached):
                yield self._cached[index]
                index += 1
            elif not self._exhausted:
                try:
                    item = next(self._iterable)
                except StopIteration:
                    self._exhausted = True
                    break
                self._cached.append(item)
                index += 1
                yield item
            else:
                break

    def __next__(self) -> Any:
        if self._next_index < len(self._cached):
            item = self._cached[self._next_index]
            self._next_index += 1
            return item
        elif not self._exhausted:
            try:
                item = next(self._iterable)
            except StopIteration:
                self._exhausted = True
                raise
            self._cached.append(item)
            self._next_index += 1
            return item
        else:
            raise StopIteration


def _wrap_iterators(val: Any) -> Any:
    if isinstance(val, (collections.abc.Iterator, collections.abc.Generator)) and not isinstance(val, _IdempotentIterable):
        return _IdempotentIterable(val)
    return val


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

    __slots__ = (
        'function',
        'validate_return',
        'schema_type',
        'module',
        'qualname',
        'ns_resolver',
        'config_wrapper',
        '__pydantic_complete__',
        '__pydantic_validator__',
        '__return_pydantic_validator__',
    )

    def __init__(
        self,
        function: ValidateCallSupportedTypes,
        config: ConfigDict | None,
        validate_return: bool,
        parent_namespace: MappingNamespace | None,
    ) -> None:
        self.function = function
        self.validate_return = validate_return
        if isinstance(function, partial):
            self.schema_type = function.func
            self.module = function.func.__module__
        else:
            self.schema_type = function
            self.module = function.__module__
        self.qualname = extract_function_qualname(function)

        self.ns_resolver = NsResolver(
            namespaces_tuple=ns_for_function(self.schema_type, parent_namespace=parent_namespace)
        )
        self.config_wrapper = ConfigWrapper(config)
        if not self.config_wrapper.defer_build:
            self._create_validators()
        else:
            self.__pydantic_complete__ = False

    def _create_validators(self) -> None:
        gen_schema = GenerateSchema(self.config_wrapper, self.ns_resolver)
        schema = gen_schema.clean_schema(gen_schema.generate_schema(self.function))
        core_config = self.config_wrapper.core_config(title=self.qualname)

        self.__pydantic_validator__ = create_schema_validator(
            schema,
            self.schema_type,
            self.module,
            self.qualname,
            'validate_call',
            core_config,
            self.config_wrapper.plugin_settings,
        )
        if self.validate_return:
            signature = signature_no_eval(self.function)
            return_type = signature.return_annotation if signature.return_annotation is not signature.empty else Any
            gen_schema = GenerateSchema(self.config_wrapper, self.ns_resolver)
            schema = gen_schema.clean_schema(gen_schema.generate_schema(return_type))
            validator = create_schema_validator(
                schema,
                self.schema_type,
                self.module,
                self.qualname,
                'validate_call',
                core_config,
                self.config_wrapper.plugin_settings,
            )
            if inspect.iscoroutinefunction(self.function):

                async def return_val_wrapper(aw: Awaitable[Any]) -> None:
                    return validator.validate_python(await aw)

                self.__return_pydantic_validator__ = return_val_wrapper
            else:
                self.__return_pydantic_validator__ = validator.validate_python
        else:
            self.__return_pydantic_validator__ = None

        self.__pydantic_complete__ = True

    def __call__(self, /, *args: Any, **kwargs: Any) -> Any:
        if not self.__pydantic_complete__:
            self._create_validators()

        args = tuple(_wrap_iterators(a) for a in args)
        kwargs = {k: _wrap_iterators(v) for k, v in kwargs.items()}

        res = self.__pydantic_validator__.validate_python(pydantic_core.ArgsKwargs(args, kwargs))
        if self.__return_pydantic_validator__:
            return self.__return_pydantic_validator__(res)
        else:
            return res
