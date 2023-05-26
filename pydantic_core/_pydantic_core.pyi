import decimal
import sys
from typing import Any, Callable

from pydantic_core import ErrorDetails, InitErrorDetails
from pydantic_core.core_schema import CoreConfig, CoreSchema, ErrorType

if sys.version_info < (3, 9):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import Literal, LiteralString, NotRequired, TypeAlias
else:
    from typing import Literal, LiteralString, NotRequired, TypeAlias

from _typeshed import SupportsAllComparisons

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
    @property
    def title(self) -> str: ...
    def __init__(self, schema: CoreSchema, config: 'CoreConfig | None' = None) -> None: ...
    def validate_python(
        self, input: Any, *, strict: 'bool | None' = None, context: Any = None, self_instance: 'Any | None' = None
    ) -> Any: ...
    def isinstance_python(
        self, input: Any, *, strict: 'bool | None' = None, context: Any = None, self_instance: 'Any | None' = None
    ) -> bool: ...
    def validate_json(
        self,
        input: 'str | bytes | bytearray',
        *,
        strict: 'bool | None' = None,
        context: Any = None,
        self_instance: 'Any | None' = None,
    ) -> Any: ...
    def validate_assignment(
        self, obj: Any, field: str, input: Any, *, strict: 'bool | None' = None, context: Any = None
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
        warnings: bool = True,
        fallback: 'Callable[[Any], Any] | None' = None,
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
        warnings: bool = True,
        fallback: 'Callable[[Any], Any] | None' = None,
    ) -> bytes: ...

def to_json(
    value: Any,
    *,
    indent: int | None = None,
    include: IncEx = None,
    exclude: IncEx = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal['iso8601', 'float'] = 'iso8601',
    bytes_mode: Literal['utf8', 'base64'] = 'utf8',
    serialize_unknown: bool = False,
    fallback: 'Callable[[Any], Any] | None' = None,
) -> bytes: ...
def to_jsonable_python(
    value: Any,
    *,
    include: IncEx = None,
    exclude: IncEx = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal['iso8601', 'float'] = 'iso8601',
    bytes_mode: Literal['utf8', 'base64'] = 'utf8',
    serialize_unknown: bool = False,
    fallback: 'Callable[[Any], Any] | None' = None,
) -> Any: ...

class Url(SupportsAllComparisons):
    @property
    def scheme(self) -> str: ...
    @property
    def username(self) -> 'str | None': ...
    @property
    def password(self) -> 'str | None': ...
    @property
    def host(self) -> 'str | None': ...
    @property
    def port(self) -> 'int | None': ...
    @property
    def path(self) -> 'str | None': ...
    @property
    def query(self) -> 'str | None': ...
    @property
    def fragment(self) -> 'str | None': ...
    def __init__(self, url: str) -> None: ...
    def unicode_host(self) -> 'str | None': ...
    def query_params(self) -> 'list[tuple[str, str]]': ...
    def unicode_string(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MultiHostHost(TypedDict):
    scheme: str
    path: 'str | None'
    query: 'str | None'
    fragment: 'str | None'

class MultiHostUrl(SupportsAllComparisons):
    @property
    def scheme(self) -> str: ...
    @property
    def path(self) -> 'str | None': ...
    @property
    def query(self) -> 'str | None': ...
    @property
    def fragment(self) -> 'str | None': ...
    def __init__(self, url: str) -> None: ...
    def hosts(self) -> 'list[MultiHostHost]': ...
    def query_params(self) -> 'list[tuple[str, str]]': ...
    def unicode_string(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class SchemaError(Exception):
    def error_count(self) -> int: ...
    def errors(self) -> 'list[ErrorDetails]': ...

class ValidationError(ValueError):
    @staticmethod
    def from_exception_data(
        title: str,
        errors: 'list[InitErrorDetails]',
        error_mode: Literal['python', 'json'] = 'python',
        hide_input: bool = False,
    ) -> ValidationError:
        """
        Provisory constructor for a Validation Error.
        This API will probably change and be deprecated in the the future; we will make it easier and more
        powerful to construct and use ValidationErrors, but we cannot do that before our initial Pydantic V2 release.
        So if you use this method please be aware that it may change or be removed before Pydantic V3.
        """
    @property
    def title(self) -> str: ...
    def error_count(self) -> int: ...
    def errors(self, *, include_url: bool = True, include_context: bool = True) -> 'list[ErrorDetails]': ...
    def json(self, *, indent: 'int | None' = None, include_url: bool = True, include_context: bool = False) -> str: ...

class PydanticCustomError(ValueError):
    def __init__(
        self, error_type: LiteralString, message_template: LiteralString, context: 'dict[str, Any] | None' = None
    ) -> None: ...
    @property
    def type(self) -> str: ...
    @property
    def message_template(self) -> str: ...
    context: 'dict[str, Any] | None'
    def message(self) -> str: ...

class PydanticKnownError(ValueError):
    @property
    def type(self) -> ErrorType: ...
    @property
    def message_template(self) -> str: ...
    context: 'dict[str, str | int | float] | None'

    def __init__(
        self, error_type: ErrorType, context: 'dict[str, str | int | float | decimal.Decimal] | None' = None
    ) -> None: ...
    def message(self) -> str: ...

class PydanticOmit(Exception):
    def __init__(self) -> None: ...

class PydanticSerializationError(ValueError):
    def __init__(self, message: str) -> None: ...

class PydanticSerializationUnexpectedValue(ValueError):
    def __init__(self, message: 'str | None' = None) -> None: ...

class ErrorTypeInfo(TypedDict):
    type: ErrorType
    message_template_python: str
    example_message_python: str
    message_template_json: NotRequired[str]
    example_message_json: NotRequired[str]
    example_context: 'dict[str, str | int | float] | None'

class ArgsKwargs:
    def __init__(self, args: 'tuple[Any, ...]', kwargs: 'dict[str, Any] | None' = None) -> None: ...
    @property
    def args(self) -> 'tuple[Any, ...]': ...
    @property
    def kwargs(self) -> 'dict[str, Any] | None': ...

def list_all_errors() -> 'list[ErrorTypeInfo]':
    """
    Get information about all built-in errors.
    """
