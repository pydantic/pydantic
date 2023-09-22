"""Usage docs: https://docs.pydantic.dev/2.3/usage/plugins#build-a-plugin

Plugin interface for Pydantic plugins, and related types.
"""
from __future__ import annotations

from typing import Any, Callable

from pydantic_core import CoreConfig, CoreSchema, ValidationError
from typing_extensions import Protocol, TypeAlias

__all__ = (
    'PydanticPluginProtocol',
    'ValidatePythonHandlerProtocol',
    'ValidateJsonHandlerProtocol',
    'ValidateStringsHandlerProtocol',
)


class PydanticPluginProtocol(Protocol):
    """Protocol defining the interface for Pydantic plugins."""

    def new_schema_validator(
        self,
        schema: CoreSchema,
        config: CoreConfig | None,
        plugin_settings: dict[str, object],
    ) -> tuple[
        ValidatePythonHandlerProtocol | None, ValidateJsonHandlerProtocol | None, ValidateStringsHandlerProtocol | None
    ]:
        """This method is called for each plugin every time a new [`SchemaValidator`][pydantic_core.SchemaValidator]
        is created.

        It should return an event handler for each of the three validation methods, or `None` if the plugin does not
        implement that method.

        Args:
            schema: The schema to validate against.
            config: The config to use for validation.
            plugin_settings: Any plugin settings.

        Returns:
            A tuple of optional event handlers for each of the three validation methods -
            `validate_python`, `validate_json`, `validate_strings`.
        """
        raise NotImplementedError('Pydantic plugins should implement `new_schema_validator`.')


class _BaseValidateHandlerProtocol(Protocol):
    """Base class for plugin callbacks protocols."""

    # on_enter is changed to be more specific on all subclasses
    on_enter: Callable[..., None]

    def on_success(self, result: Any) -> None:
        """Callback to be notified of successful validation.

        Args:
            result: The result of the validation.
        """
        pass

    def on_error(self, error: ValidationError) -> None:
        """Callback to be notified of validation errors.

        Args:
            error: The validation error.
        """
        pass


class ValidatePythonHandlerProtocol(_BaseValidateHandlerProtocol, Protocol):
    """Event handler for `SchemaValidator.validate_python`."""

    def on_enter(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Callback to be notified of validation start.

        Args:
            input: The input to be validated.
            strict: Whether to validate the object in strict mode.
            from_attributes: Whether to validate objects as inputs by extracting attributes.
            context: The context to use for validation, this is passed to functional validators.
            self_instance: An instance of a model to set attributes on from validation, this is used when running
                validation from the `__init__` method of a model.
        """
        pass


class ValidateJsonHandlerProtocol(_BaseValidateHandlerProtocol, Protocol):
    """Event handler for `SchemaValidator.validate_json`."""

    def on_enter(
        self,
        input: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        """Callback to be notified of validation start.

        Args:
            input: The JSON data to be validated.
            strict: Whether to validate the object in strict mode.
            context: The context to use for validation, this is passed to functional validators.
            self_instance: An instance of a model to set attributes on from validation, this is used when running
                validation from the `__init__` method of a model.
        """
        pass


StringInput: TypeAlias = 'dict[str, StringInput]'


class ValidateStringsHandlerProtocol(_BaseValidateHandlerProtocol, Protocol):
    """Event handler for `SchemaValidator.validate_strings`."""

    def on_enter(
        self, input: StringInput, *, strict: bool | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """Callback to be notified of validation start.

        Args:
            input: The string data to be validated.
            strict: Whether to validate the object in strict mode.
            context: The context to use for validation, this is passed to functional validators.
        """
        pass
