"""Meta tests, testing the test utils and fixtures."""

import pytest
from typing_extensions import Annotated

from pydantic import TypeAdapter
from pydantic.json_schema import WithJsonSchema


@pytest.mark.xfail(reason='Invalid JSON Schemas are expected to fail.')
def test_invalid_json_schema_raises() -> None:
    TypeAdapter(Annotated[int, WithJsonSchema({'type': 'invalid'})]).json_schema()
