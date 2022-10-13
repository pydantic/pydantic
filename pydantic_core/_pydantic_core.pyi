import sys
from typing import Any, TypedDict

from pydantic_core.core_schema import CoreConfig, CoreSchema, ErrorKind

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

__all__ = (
    '__version__',
    'SchemaValidator',
    'SchemaError',
    'ValidationError',
    'PydanticCustomError',
    'PydanticKindError',
    'PydanticOmit',
)
__version__: str
build_profile: str

class SchemaValidator:
    title: str
    def __init__(self, schema: CoreSchema, config: 'CoreConfig | None' = None) -> None: ...
    def validate_python(self, input: Any, strict: 'bool | None' = None, context: Any = None) -> Any: ...
    def isinstance_python(self, input: Any, strict: 'bool | None' = None, context: Any = None) -> bool: ...
    def validate_json(
        self, input: 'str | bytes | bytearray', strict: 'bool | None' = None, context: Any = None
    ) -> Any: ...
    def isinstance_json(
        self, input: 'str | bytes | bytearray', strict: 'bool | None' = None, context: Any = None
    ) -> bool: ...
    def validate_assignment(
        self, field: str, input: Any, data: 'dict[str, Any]', strict: 'bool | None' = None, context: Any = None
    ) -> 'dict[str, Any]': ...

class SchemaError(Exception):
    pass

class ErrorDetails(TypedDict):
    kind: str
    loc: 'list[int | str]'
    message: str
    input_value: Any
    context: NotRequired['dict[str, str | int | float]']

class ValidationError(ValueError):
    title: str

    def error_count(self) -> int: ...
    def errors(self, include_context: bool = True) -> 'list[ErrorDetails]': ...

class PydanticCustomError(ValueError):
    kind: str
    message_template: str
    context: 'dict[str, str | int] | None'

    def __init__(self, kind: str, message_template: str, context: 'dict[str, str | int] | None' = None) -> None: ...
    def message(self) -> str: ...

class PydanticKindError(ValueError):
    kind: ErrorKind
    message_template: str
    context: 'dict[str, str | int] | None'

    def __init__(self, kind: ErrorKind, context: 'dict[str, str | int] | None' = None) -> None: ...
    def message(self) -> str: ...

class PydanticOmit(Exception):
    def __init__(self) -> None: ...

class ErrorKindInfo(TypedDict):
    kind: ErrorKind
    message_template: str
    example_message: str
    example_context: 'dict[str, str | int | float] | None'

def list_all_errors() -> 'list[ErrorKindInfo]':
    """
    Get information about all built-in errors.
    """
