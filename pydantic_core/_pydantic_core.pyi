import sys
from typing import Any, TypedDict

from pydantic_core._types import Config, Schema

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

__all__ = '__version__', 'SchemaValidator', 'SchemaError', 'ValidationError', 'PydanticValueError'
__version__: str

class SchemaValidator:
    def __init__(self, schema: Schema, config: 'Config | None' = None) -> None: ...
    def validate_python(self, input: Any, strict: 'bool | None' = None, context: Any = None) -> Any: ...
    def isinstance_python(self, input: Any, strict: 'bool | None' = None, context: Any = None) -> bool: ...
    def validate_json(
        self, input: 'str | bytes | bytearray', strict: 'bool | None' = None, context: Any = None
    ) -> Any: ...
    def isinstance_json(
        self, input: 'str | bytes | bytearray', strict: 'bool | None' = None, context: Any = None
    ) -> bool: ...
    def validate_assignment(self, field: str, input: Any, data: 'dict[str, Any]') -> 'dict[str, Any]': ...

class SchemaError(Exception):
    pass

class ErrorDetails(TypedDict):
    kind: str
    loc: 'list[int | str]'
    message: str
    input_value: Any
    context: NotRequired['dict[str, Any]']

class ValidationError(ValueError):
    title: str

    def error_count(self) -> int: ...
    def errors(self) -> 'list[ErrorDetails]': ...

class PydanticValueError(ValueError):
    kind: str
    message_template: str
    context: 'dict[str, str | int] | None'

    def __init__(self, kind: str, message_template: str, context: 'dict[str, str | int] | None' = None) -> None: ...
    def message(self) -> str: ...
