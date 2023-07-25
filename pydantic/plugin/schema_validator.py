"""Pluggable schema validator for pydantic."""
from __future__ import annotations

import contextlib
import functools
from typing import Any, Callable, Final, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import Literal, ParamSpec

from .loader import plugins
from .plugin import Step

P = ParamSpec('P')
R = TypeVar('R')


def schema_validator_cls() -> type[SchemaValidator]:
    """Get the schema validator class.

    Returns:
        type[SchemaValidator]: If plugins are installed then return `PluggableSchemaValidator`,
            otherwise return `SchemaValidator`.
    """
    return PluggableSchemaValidator if plugins else SchemaValidator  # type: ignore


class _Plug:
    """Pluggable schema validator."""

    EVENTS: Final = {'validate_json': 'on_validate_json', 'validate_python': 'on_validate_python'}
    """Events for plugins."""

    def __init__(self, schema: CoreSchema, config: CoreConfig | None = None) -> None:
        self.schema = schema
        self.config = config

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Call plugins for pydantic."""
        enter = self.prepare_enter(func)
        on_success = self.prepare_on_success(func)
        on_error = self.prepare_on_error(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            enter(*args, **kwargs)
            try:
                result = func(*args, **kwargs)
            except ValidationError as error:
                on_error(error)
                raise
            else:
                on_success(result)
                return result

        return wrapper

    def prepare_enter(self, func: Callable[..., Any]) -> Callable[..., None]:
        enter_calls = self.gather_calls(func, callback='enter')

        def enter(*args: Any, **kwargs: Any) -> None:
            for enter_call in enter_calls:
                enter_call(*args, **kwargs)

        return enter

    def prepare_on_success(self, func: Callable[..., Any]) -> Callable[[Any], None]:
        success_calls = self.gather_calls(func, callback='on_success')

        def on_success(result: Any) -> None:
            for success_call in success_calls:
                success_call(result)

        return on_success

    def prepare_on_error(self, func: Callable[..., Any]) -> Callable[[ValidationError], None]:
        error_calls = self.gather_calls(func, callback='on_error')

        def on_error(error: ValidationError) -> None:
            for error_call in error_calls:
                error_call(error)

        return on_error

    def gather_calls(
        self, func: Callable[..., Any], callback: Literal['enter', 'on_success', 'on_error']
    ) -> list[Callable[..., None]]:
        try:
            step = self.EVENTS[func.__name__]
        except KeyError as exc:
            raise RuntimeError(f'Unknown event for {func.__name__}') from exc

        calls: list[Callable[..., None]] = []
        for plugin in plugins:
            with contextlib.suppress(AttributeError, TypeError):
                step_type: type[Step] = getattr(plugin, step)
                on_step = step_type(schema=self.schema, config=self.config)
                calls.append(getattr(on_step, callback))

        return calls


class PluggableSchemaValidator:
    """Pluggable schema validator."""

    def __init__(self, schema: CoreSchema, config: CoreConfig | None = None) -> None:
        self.schema_validator = SchemaValidator(schema=schema, config=config)

        self.plug = _Plug(schema=schema, config=config)

        self.validate_json = self.plug(self.schema_validator.validate_json)
        self.validate_python = self.plug(self.schema_validator.validate_python)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.schema_validator, name)
