"""Pluggable schema validator for pydantic."""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable, Iterable, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import Literal, ParamSpec

if TYPE_CHECKING:
    from . import PydanticPluginProtocol, _BaseValidateHandlerProtocol


P = ParamSpec('P')
R = TypeVar('R')
Event = Literal['on_validate_python', 'on_validate_json', 'on_validate_strings']
events: list[Event] = list(Event.__args__)  # type: ignore


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

    __slots__ = '_schema_validator', 'validate_json', 'validate_python', 'validate_strings'

    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugins: Iterable[PydanticPluginProtocol],
        plugin_settings: dict[str, Any],
    ) -> None:
        self._schema_validator = SchemaValidator(schema, config)

        python_event_handlers: list[_BaseValidateHandlerProtocol] = []
        json_event_handlers: list[_BaseValidateHandlerProtocol] = []
        strings_event_handlers: list[_BaseValidateHandlerProtocol] = []
        for plugin in plugins:
            p, j, s = plugin.new_schema_validator(schema, config, plugin_settings)
            if p is not None:
                python_event_handlers.append(p)
            if j is not None:
                json_event_handlers.append(j)
            if s is not None:
                strings_event_handlers.append(s)

        self.validate_python = build_wrapper(self._schema_validator.validate_python, python_event_handlers)
        self.validate_json = build_wrapper(self._schema_validator.validate_json, json_event_handlers)
        self.validate_strings = build_wrapper(self._schema_validator.validate_strings, strings_event_handlers)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._schema_validator, name)


def build_wrapper(func: Callable[P, R], event_handlers: list[_BaseValidateHandlerProtocol]) -> Callable[P, R]:
    if not event_handlers:
        return func
    else:

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for handler in event_handlers:
                handler.on_enter(*args, **kwargs)

            try:
                result = func(*args, **kwargs)
            except ValidationError as error:
                for handler in event_handlers:
                    handler.on_error(error)
                raise
            else:
                for handler in event_handlers:
                    handler.on_success(result)
                return result

        return wrapper
