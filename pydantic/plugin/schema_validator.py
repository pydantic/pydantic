"""Pluggable schema validator for pydantic."""
from __future__ import annotations

import contextlib
import functools
from enum import Enum
from typing import Any, Callable, Iterator, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import Literal, ParamSpec

from .plugin import EventHandler, Plugin

P = ParamSpec('P')
R = TypeVar('R')


def create_schema_validator(
    schema: CoreSchema, config: CoreConfig | None = None, plugin_settings: dict[str, Any] | None = None
) -> SchemaValidator:
    """Get the schema validator class.

    Returns:
        If plugins are installed then return `PluggableSchemaValidator`, otherwise return `SchemaValidator`.
    """
    from ._loader import plugins

    if plugins:
        return PluggableSchemaValidator(schema, config, plugins, plugin_settings or {})  # type: ignore
    return SchemaValidator(schema, config)


class PluggableSchemaValidator:
    """Pluggable schema validator."""

    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: set[Plugin],
        plugin_settings: dict[str, Any],
    ) -> None:
        self.schema_validator = SchemaValidator(schema, config)

        self.plugin_factory = _PluginFactory(schema, config, plugins, plugin_settings)

        self.validate_json = self.plugin_factory(self.schema_validator.validate_json)
        self.validate_python = self.plugin_factory(self.schema_validator.validate_python)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.schema_validator, name)


class _PluginFactory:
    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: set[Plugin],
        plugin_settings: dict[str, Any],
    ) -> None:
        self.schema = schema
        self.config = config
        self.plugins = plugins
        self.plugin_settings = plugin_settings

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        """Call plugins for pydantic"""
        try:
            event = _Event[func.__name__]
        except KeyError as exc:
            raise RuntimeError(f'Unknown event for {func.__name__}') from exc

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            plugin_api = self.plugin_api(event=event)

            plugin_api.on_enter(*args, **kwargs)
            try:
                result = func(*args, **kwargs)
            except ValidationError as error:
                plugin_api.on_error(error)
                raise
            else:
                plugin_api.on_success(result)
                return result

        return wrapper

    def plugin_api(self, event: _Event) -> _PluginAPI:
        return _PluginAPI(
            event=event,
            schema=self.schema,
            config=self.config,
            plugins=self.plugins,
            plugin_settings=self.plugin_settings,
        )


class _PluginAPI:
    def __init__(
        self,
        event: _Event,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: set[Plugin],
        plugin_settings: dict[str, Any],
    ) -> None:
        self.event = event

        self.schema = schema
        self.config = config
        self.plugin_settings = plugin_settings

        self.event_handlers = self.prepare_event_handlers(plugins)

        self.on_enter = self.prepare_on_enter()
        self.on_success = self.prepare_on_success()
        self.on_error = self.prepare_on_error()

        self._in_call: set[str] = set()

    def prepare_event_handlers(self, plugins: set[Plugin]) -> list[EventHandler]:
        handlers: list[EventHandler] = []

        for plugin in plugins:
            if not hasattr(plugin, self.event.value):
                continue
            handler_type: type[EventHandler] = getattr(plugin, self.event.value)
            handlers.append(handler_type(self.schema, self.config, self.plugin_settings))

        return handlers

    def prepare_on_enter(self) -> Callable[..., None]:
        enter_calls = self.gather_calls(callback_type='on_enter')
        return self.run_callbacks(enter_calls)

    def prepare_on_success(self) -> Callable[[Any], None]:
        success_calls = self.gather_calls(callback_type='on_success')
        return self.run_callbacks(success_calls)

    def prepare_on_error(self) -> Callable[[ValidationError], None]:
        error_calls = self.gather_calls(callback_type='on_error')
        return self.run_callbacks(error_calls)

    def run_callbacks(self, callbacks: list[Callable[..., None]]) -> Callable[..., None]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            for callback in callbacks:
                with self.run_once(callback) as callback_once:
                    if callback_once is None:
                        continue
                    callback_once(*args, **kwargs)

        return wrapper

    def gather_calls(self, callback_type: Literal['on_enter', 'on_success', 'on_error']) -> list[Callable[..., None]]:
        calls: list[Callable[..., None]] = []

        for handler in self.event_handlers:
            if not hasattr(handler, callback_type):
                continue
            calls.append(getattr(handler, callback_type))

        return calls

    @contextlib.contextmanager
    def run_once(self, func: Callable[..., Any]) -> Iterator[Callable[..., Any] | None]:
        _callback_key = func.__qualname__

        if _callback_key in self._in_call:
            yield None
            return

        self._in_call.add(_callback_key)
        yield func
        self._in_call.remove(_callback_key)


class _Event(str, Enum):
    """Events for plugins"""

    validate_json = 'on_validate_json'
    validate_python = 'on_validate_python'
