"""Meta tests, testing the test utils and fixtures."""

import sys
from typing import Annotated

import pytest

from pydantic import TypeAdapter
from pydantic.json_schema import WithJsonSchema


@pytest.mark.xfail(
    # See comment in `validate_json_schemas()` fixture:
    condition=sys.platform != 'emscripten',
    reason='Invalid JSON Schemas are expected to fail.',
)
def test_invalid_json_schema_raises() -> None:
    TypeAdapter(Annotated[int, WithJsonSchema({'type': 'invalid'})]).json_schema()
