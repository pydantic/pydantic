import json
from dataclasses import dataclass
from typing import Any

import pytest

from pydantic_core import SchemaValidator

__all__ = ('Err',)


@dataclass
class Err:
    message: str
    errors: Any = None


@pytest.fixture(params=['python', 'json'])
def py_or_json(request):
    class CustomSchemaValidator:
        def __init__(self, schema):
            self.validator = SchemaValidator(schema)

        def validate_test(self, py_input):
            if request.param == 'json':
                return self.validator.validate_json(json.dumps(py_input))
            else:
                return self.validator.validate_python(py_input)

    return CustomSchemaValidator
