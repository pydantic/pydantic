"""Plugin interface for Pydantic plugins, and related types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from pydantic_core import ValidationError
from typing_extensions import Protocol

T = TypeVar('T', bound=Callable[..., None])


class OnSuccess(Protocol):
    """Protocol for `on_success` callback."""

    def __call__(self, result: Any) -> None:  # noqa: D102
        ...


class OnError(Protocol):
    """Protocol for `on_error` callback."""

    def __call__(self, error: ValidationError) -> None:  # noqa: D102
        ...


@dataclass
class Step(Generic[T]):
    """Step for plugin callbacks."""

    enter: T | None = None
    on_success: OnSuccess | None = None
    on_error: OnError | None = None


class ValidatePythonEnter(Protocol):
    """Protocol for `on_validate_python` callback."""

    def __call__(  # noqa: D102
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        ...


class ValidateJsonEnter(Protocol):
    """Protocol for `on_validate_json` callback."""

    def __call__(  # noqa: D102
        self,
        input: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        ...


OnValidatePython = Step[ValidatePythonEnter]
OnValidateJson = Step[ValidateJsonEnter]


@dataclass
class Plugin:
    """Plugin interface for Pydantic plugins."""

    on_validate_python: OnValidatePython | None = None
    on_validate_json: OnValidateJson | None = None
