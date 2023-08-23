"""Usage docs: https://docs.pydantic.dev/dev-v2/integrations/plugins#build-a-plugin

Plugin interface for Pydantic plugins, and related types.
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic_core import CoreConfig, CoreSchema, ValidationError


class Step:
    """Step for plugin callbacks."""

    def __init__(
        self,
        schema: CoreSchema,
        config: CoreConfig | None = None,
        plugin_settings: dict[str, object] | None = None,
    ) -> None:
        self.schema = schema
        self.config = config
        self.plugin_settings = plugin_settings

    @abstractmethod
    def on_success(self, result: Any) -> None:
        """Call `on_success` callback."""
        raise NotImplementedError()

    @abstractmethod
    def on_error(self, error: ValidationError) -> None:
        """Call `on_error` callback."""
        raise NotImplementedError()


class OnValidatePython(Step):
    """`on_validate_python` step callback."""

    @abstractmethod
    def enter(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Call `enter` callback."""
        raise NotImplementedError()


class OnValidateJson(Step):
    """`on_validate_json` step callback."""

    @abstractmethod
    def enter(
        self,
        input: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Call `enter` callback."""
        raise NotImplementedError()


@dataclass(frozen=True)
class Plugin:
    """Usage docs: https://docs.pydantic.dev/2.2/integrations/plugins/

    Plugin interface for Pydantic plugins.
    """

    on_validate_python: type[OnValidatePython] | None = None
    on_validate_json: type[OnValidateJson] | None = None
