import sys
from typing import Any, Dict, List, Optional, TypedDict, Union

from pydantic_core._types import Config, Schema

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

__all__ = '__version__', 'SchemaValidator', 'SchemaError', 'ValidationError', 'PydanticValueError'
__version__: str

class SchemaValidator:
    def __init__(self, schema: Schema, config: Optional[Config] = None) -> None: ...
    def validate_python(self, input: Any, strict: Optional[bool] = None, context: Any = None) -> Any: ...
    def isinstance_python(self, input: Any, strict: Optional[bool] = None, context: Any = None) -> bool: ...
    def validate_json(
        self, input: Union[str, bytes, bytearray], strict: Optional[bool] = None, context: Any = None
    ) -> Any: ...
    def isinstance_json(
        self, input: Union[str, bytes, bytearray], strict: Optional[bool] = None, context: Any = None
    ) -> bool: ...
    def validate_assignment(self, field: str, input: Any, data: Dict[str, Any]) -> Dict[str, Any]: ...

class SchemaError(Exception):
    pass

class ErrorDetails(TypedDict):
    kind: str
    loc: List[Union[int, str]]
    message: str
    input_value: Any
    context: NotRequired[Dict[str, Any]]

class ValidationError(ValueError):
    title: str

    def error_count(self) -> int: ...
    def errors(self) -> List[ErrorDetails]: ...

class PydanticValueError(ValueError):
    kind: str
    message_template: str
    context: Optional[Dict[str, Union[str, int]]]

    def __init__(
        self, kind: str, message_template: str, context: Optional[Dict[str, Union[str, int]]] = None
    ) -> None: ...
    def message(self) -> str: ...
