"""Pluggable schema validator for pydantic."""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from . import BaseValidateHandlerProtocol, PydanticPluginProtocol, SchemaKind, SchemaTypePath


P = ParamSpec('P')
R = TypeVar('R')
Event = Literal['on_validate_python', 'on_validate_json', 'on_validate_strings']
events: list[Event] = list(Event.__args__)  # type: ignore


def create_schema_validator(
    schema: CoreSchema,
    schema_type: Any,
    schema_type_module: str,
    schema_type_name: str,
    schema_kind: SchemaKind,
    config: CoreConfig | None = None,
    plugin_settings: dict[str, Any] | None = None,
    _use_prebuilt: bool = True,
) -> SchemaValidator | PluggableSchemaValidator:
    """Create a `SchemaValidator` or `PluggableSchemaValidator` if plugins are installed.

    Returns:
        If plugins are installed then return `PluggableSchemaValidator`, otherwise return `SchemaValidator`.
    """
    from . import SchemaTypePath
    from ._loader import get_plugins

    plugins = get_plugins()
    if plugins:
        pluggable_schema_validator = PluggableSchemaValidator(
            schema,
            schema_type,
            SchemaTypePath(schema_type_module, schema_type_name),
            schema_kind,
            config,
            plugins,
            plugin_settings or {},
            _use_prebuilt=_use_prebuilt,
        )
        if pluggable_schema_validator._has_event_handlers:
            return pluggable_schema_validator
        else:
            # No plugin provided any event handler for this schema, so the wrapper is functionally
            # inert. Return the underlying `SchemaValidator` instead: an unnecessary wrapper isn't
            # free — in particular, it prevents `pydantic-core` from reusing the already built
            # validator when other models reference this schema's type (which can massively
            # increase memory usage in applications with many interconnected models).
            return pluggable_schema_validator._schema_validator
    else:
        return SchemaValidator(schema, config, _use_prebuilt=_use_prebuilt)


class PluggableSchemaValidator:
    """Pluggable schema validator."""

    __slots__ = '_schema_validator', '_has_event_handlers', 'validate_json', 'validate_python', 'validate_strings'

    def __init__(
        self,
        schema: CoreSchema,
        schema_type: Any,
        schema_type_path: SchemaTypePath,
        schema_kind: SchemaKind,
        config: CoreConfig | None,
        plugins: Iterable[PydanticPluginProtocol],
        plugin_settings: dict[str, Any],
        _use_prebuilt: bool = True,
    ) -> None:
        self._schema_validator = SchemaValidator(schema, config, _use_prebuilt=_use_prebuilt)

        python_event_handlers: list[BaseValidateHandlerProtocol] = []
        json_event_handlers: list[BaseValidateHandlerProtocol] = []
        strings_event_handlers: list[BaseValidateHandlerProtocol] = []
        for plugin in plugins:
            try:
                p, j, s = plugin.new_schema_validator(
                    schema, schema_type, schema_type_path, schema_kind, config, plugin_settings
                )
            except TypeError as e:  # pragma: no cover
                raise TypeError(f'Error using plugin `{plugin.__module__}:{plugin.__class__.__name__}`: {e}') from e
            if p is not None:
                python_event_handlers.append(p)
            if j is not None:
                json_event_handlers.append(j)
            if s is not None:
                strings_event_handlers.append(s)

        self._has_event_handlers = bool(python_event_handlers or json_event_handlers or strings_event_handlers)
        self.validate_python = build_wrapper(self._schema_validator.validate_python, python_event_handlers)
        self.validate_json = build_wrapper(self._schema_validator.validate_json, json_event_handlers)
        self.validate_strings = build_wrapper(self._schema_validator.validate_strings, strings_event_handlers)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._schema_validator, name)


def build_wrapper(func: Callable[P, R], event_handlers: list[BaseValidateHandlerProtocol]) -> Callable[P, R]:
    if not event_handlers:
        return func
    else:
        on_enters = tuple(h.on_enter for h in event_handlers if filter_handlers(h, 'on_enter'))
        on_successes = tuple(h.on_success for h in event_handlers if filter_handlers(h, 'on_success'))
        on_errors = tuple(h.on_error for h in event_handlers if filter_handlers(h, 'on_error'))
        on_exceptions = tuple(h.on_exception for h in event_handlers if filter_handlers(h, 'on_exception'))

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for on_enter_handler in on_enters:
                on_enter_handler(*args, **kwargs)

            try:
                result = func(*args, **kwargs)
            except ValidationError as error:
                for on_error_handler in on_errors:
                    on_error_handler(error)
                raise
            except Exception as exception:
                for on_exception_handler in on_exceptions:
                    on_exception_handler(exception)
                raise
            else:
                for on_success_handler in on_successes:
                    on_success_handler(result)
                return result

        return wrapper


def filter_handlers(handler_cls: BaseValidateHandlerProtocol, method_name: str) -> bool:
    """Filter out handler methods which are not implemented by the plugin directly - e.g. those that are missing
    or are inherited from the protocol.
    """
    handler = getattr(handler_cls, method_name, None)
    if handler is None:
        return False
    elif handler.__module__ == 'pydantic.plugin':
        # this is the original handler, from the protocol due to runtime inheritance
        # we don't want to call it
        return False
    else:
        return True
