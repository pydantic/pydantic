from typing import Any, Dict

__version__: str

class SchemaValidator:
    def __init__(self, schema: Dict[str, Any]) -> None: ...
    def run(self, data: Any) -> Dict[str, Any]: ...
