import decimal
import sys
from typing import Any, TypedDict

from pydantic_core.core_schema import CoreConfig, CoreSchema, ErrorType

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, TypeAlias
else:
    from typing import NotRequired, TypeAlias

__all__ = (
    '__version__',
    'build_profile',
    'SchemaValidator',
    'SchemaSerializer',
    'Url',
    'MultiHostUrl',
    'SchemaError',
    'ValidationError',
    'PydanticCustomError',
    'PydanticKnownError',
    'PydanticOmit',
    'PydanticSerializationError',
    'list_all_errors',
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

IncEx: TypeAlias = 'set[int] | set[str] | dict[int, IncEx] | dict[str, IncEx] | None'

class SchemaSerializer:
    def __init__(self, schema: CoreSchema, config: 'CoreConfig | None' = None) -> None: ...
    def to_python(
        self,
        value: Any,
        *,
        mode: str | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
    ) -> Any: ...
    def to_json(
        self,
        value: Any,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
    ) -> bytes: ...

class Url:
    scheme: str
    username: 'str | None'
    password: 'str | None'
    host: 'str | None'
    port: 'int | None'
    path: 'str | None'
    query: 'str | None'
    fragment: 'str | None'

    def unicode_host(self) -> 'str | None': ...
    def query_params(self) -> 'list[tuple[str, str]]': ...
    def unicode_string(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MultiHostHost(TypedDict):
    username: 'str | None'
    password: 'str | None'
    host: str
    port: 'int | None'

class MultiHostUrl:
    scheme: str
    path: 'str | None'
    query: 'str | None'
    fragment: 'str | None'

    def hosts(self) -> 'list[MultiHostHost]': ...
    def query_params(self) -> 'list[tuple[str, str]]': ...
    def unicode_string(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class SchemaError(Exception):
    pass

class ErrorDetails(TypedDict):
    type: str
    loc: 'tuple[int | str, ...]'
    msg: str
    input: Any
    ctx: NotRequired['dict[str, str | int | float]']

class ValidationError(ValueError):
    title: str

    def error_count(self) -> int: ...
    def errors(self, include_context: bool = True) -> 'list[ErrorDetails]': ...

class PydanticCustomError(ValueError):
    type: str
    message_template: str
    context: 'dict[str, Any] | None'

    def __init__(self, error_type: str, message_template: str, context: 'dict[str, Any] | None' = None) -> None: ...
    def message(self) -> str: ...

class PydanticKnownError(ValueError):
    type: ErrorType
    message_template: str
    context: 'dict[str, str | int | float] | None'

    def __init__(
        self, error_type: ErrorType, context: 'dict[str, str | int | float | decimal.Decimal] | None' = None
    ) -> None: ...
    def message(self) -> str: ...

class PydanticOmit(Exception):
    def __init__(self) -> None: ...

class PydanticSerializationError(ValueError):
    def __init__(self, message: str) -> None: ...

class ErrorTypeInfo(TypedDict):
    type: ErrorType
    message_template: str
    example_message: str
    example_context: 'dict[str, str | int | float] | None'

def list_all_errors() -> 'list[ErrorTypeInfo]':
    """
    Get information about all built-in errors.
    """
