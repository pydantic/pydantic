from typing import Any, Dict, List

__version__: str

class SchemaValidator:
    def __init__(self, schema: Dict[str, Any]) -> None: ...
    def run(self, data: Any) -> Dict[str, Any]: ...

class SchemaError(ValueError):
    pass

class ValidationError(ValueError):
    model_name: str

    def error_count(self) -> int: ...
    def errors(self) -> List[Dict[str, Any]]: ...
