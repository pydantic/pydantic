from typing import Any, Dict, List

__version__: str

class SchemaValidator:
    def __init__(self, schema: Dict[str, Any]) -> None: ...
    def run(self, input: Any) -> Dict[str, Any]: ...
    def run_assignment(self, field: str, input: Any, data: Dict[str, Any]) -> Dict[str, Any]: ...

class SchemaError(ValueError):
    pass

class ValidationError(ValueError):
    model_name: str

    def error_count(self) -> int: ...
    def errors(self) -> List[Dict[str, Any]]: ...
