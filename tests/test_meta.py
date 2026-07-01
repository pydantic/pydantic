"""Meta tests, testing the test utils and fixtures."""

import sys
from typing import Annotated

import pytest

from pydantic import TypeAdapter
from pydantic.json_schema import WithJsonSchema


@pytest.mark.xfail(
    # See comment in `validate_json_schemas()` fixture in conftest.py:
    # On non-emscripten, the test fixture fails the test when the emitted schema is invalid
    # (pytest.fail / SchemaError path). That outcome is *expected* today (xfail), documenting
    # that invalid WithJsonSchema is caught at test time via meta-schema validation rather than
    # always raising from TypeAdapter.json_schema() itself. Remove xfail when product behavior
    # or the fixture policy changes intentionally.
    condition=sys.platform != 'emscripten',
    reason='Invalid JSON Schemas are expected to fail under the test JSON Schema validator fixture.',
)
def test_invalid_json_schema_raises() -> None:
    """Emits an invalid JSON Schema; suite fixture should reject it (xfail on desktop CI)."""
    TypeAdapter(Annotated[int, WithJsonSchema({'type': 'invalid'})]).json_schema()
