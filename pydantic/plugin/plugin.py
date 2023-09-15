"""Usage docs: https://docs.pydantic.dev/2.3/usage/plugins#build-a-plugin

Plugin interface for Pydantic plugins, and related types.
"""
from __future__ import annotations

from typing import Any

from pydantic_core import CoreConfig, CoreSchema, ValidationError
from typing_extensions import Protocol


class _EventHandlerProtocol(Protocol):
    """Event handler Protocol and base class for plugin callbacks."""

    schema: CoreSchema
    config: CoreConfig | None
    plugin_settings: dict[str, object]

    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugin_settings: dict[str, object],
    ) -> None:
        self.schema = schema
        self.config = config
        self.plugin_settings = plugin_settings

    def on_success(self, result: Any) -> None:
        """Call `on_success` callback."""
        pass

    def on_error(self, error: ValidationError) -> None:
        """Call `on_error` callback."""
        pass


class OnValidatePythonProtocol(_EventHandlerProtocol, Protocol):
    """`on_validate_python` event handler Protocol."""

    def on_enter(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Call `enter` callback."""
        pass


class OnValidateJsonProtocol(_EventHandlerProtocol, Protocol):
    """`on_validate_json` event handler Protocol."""

    def on_enter(
        self,
        input: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Call `enter` callback."""
        pass


class PydanticPlugin(Protocol):
    """Plugin interface for Pydantic plugins"""

    on_validate_python: type[OnValidatePythonProtocol] | None = None
    on_validate_json: type[OnValidateJsonProtocol] | None = None
