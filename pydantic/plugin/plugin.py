from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from pydantic_core import ValidationError

T = TypeVar('T', bound=Callable[..., None])


class OnSuccess(Protocol):
    def __call__(self, result: Any) -> None:
        ...


class OnError(Protocol):
    def __call__(self, error: ValidationError) -> None:
        ...


@dataclass
class Step(Generic[T]):
    enter: T | None = None
    on_success: OnSuccess | None = None
    on_error: OnError | None = None


class ValidatePythonEnter(Protocol):
    def __call__(
        self,
        cls: type[Any],  # type: ignore
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ...


class ValidateJsonEnter(Protocol):
    def __call__(
        self,
        cls: type[Any],  # type: ignore
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ...


OnValidatePython = Step[ValidatePythonEnter]
OnValidateJson = Step[ValidateJsonEnter]


@dataclass
class Plugin:
    on_validate_python: OnValidatePython | None = None
    on_validate_json: OnValidateJson | None = None
