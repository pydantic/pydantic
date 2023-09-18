"""Pluggable schema validator for pydantic."""
from __future__ import annotations

import contextlib
import functools
import warnings
from enum import Enum
from typing import Any, Callable, ClassVar, Iterator, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import Literal, ParamSpec

from .plugin import PydanticPlugin, _EventHandlerProtocol

P = ParamSpec('P')
R = TypeVar('R')


def create_schema_validator(
    schema: CoreSchema, config: CoreConfig | None = None, plugin_settings: dict[str, Any] | None = None
) -> SchemaValidator:
    """Create a `SchemaValidator` or `PluggableSchemaValidator` if plugins are installed.

    Returns:
        If plugins are installed then return `PluggableSchemaValidator`, otherwise return `SchemaValidator`.
    """
    from ._loader import get_plugins

    plugins = get_plugins()
    if plugins:
        return PluggableSchemaValidator(schema, config, plugins, plugin_settings or {})  # type: ignore
    else:
        return SchemaValidator(schema, config)


class PluggableSchemaValidator:
    """Pluggable schema validator."""

    __slots__ = '_schema_validator', 'validate_json', 'validate_python'

    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: set[PydanticPlugin],
        plugin_settings: dict[str, Any],
    ) -> None:
        self._schema_validator = SchemaValidator(schema, config)

        def plugin_api_builder(event: _Event) -> _PluginAPI:
            return _PluginAPI(
                event=event, schema=schema, config=config, plugins=plugins, plugin_settings=plugin_settings
            )

        self.validate_json = self._build_wrapper(self._schema_validator.validate_json, plugin_api_builder)
        self.validate_python = self._build_wrapper(self._schema_validator.validate_python, plugin_api_builder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._schema_validator, name)

    def _build_wrapper(
        self, func: Callable[P, R], plugin_api_builder: Callable[[_Event], _PluginAPI]
    ) -> Callable[P, R]:
        try:
            event = _Event[func.__name__]
        except KeyError as exc:
            raise RuntimeError(f'Unknown event for {func.__name__}') from exc

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            plugin_api = plugin_api_builder(event)

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


class _PluginAPI:
    """Creates Event Handlers instances for each validation call.

    Provides a single accumulated callback for each validation hook.
    """

    _in_call: ClassVar[set[str]] = set()

    def __init__(
        self,
        event: _Event,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: set[PydanticPlugin],
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

    def prepare_event_handlers(self, plugins: set[PydanticPlugin]) -> list[_EventHandlerProtocol]:
        handlers: list[_EventHandlerProtocol] = []

        for plugin in plugins:
            handler_type: type[_EventHandlerProtocol] | None = getattr(plugin, self.event.value)
            if handler_type is None:
                continue
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
                    try:
                        callback_once(*args, **kwargs)
                    except ImportError as e:  # It could be an ImportError or an AttributeError
                        warnings.warn(f'Error while running a Pydantic plugin {callback.__code__.co_filename!r}: {e}')

        return wrapper

    def gather_calls(self, callback_type: Literal['on_enter', 'on_success', 'on_error']) -> list[Callable[..., None]]:
        calls: list[Callable[..., None]] = []

        for handler_name in self.event_handlers:
            handler = getattr(handler_name, callback_type, None)
            if handler is None:
                continue
            calls.append(handler)

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
