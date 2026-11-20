"""JSON string scores must agree between cursor and ordinary union branches."""

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

import pytest
from pydantic_core import SchemaValidator, core_schema

from pydantic import TypeAdapter


class TextChoice(StrEnum):
    first = 'a'


@pytest.mark.parametrize('strict', [False, True])
@pytest.mark.parametrize(
    'schema, data, expected',
    [
        (list[str] | list[UUID], '["12345678-1234-5678-1234-567812345678"]', UUID),
        (list[UUID] | list[str], '["12345678-1234-5678-1234-567812345678"]', UUID),
        (list[str] | list[date], '["2026-11-20"]', str),
        (list[date] | list[str], '["2026-11-20"]', date),
        (list[str] | list[datetime], '["2026-11-20T12:30:00"]', str),
        (list[datetime] | list[str], '["2026-11-20T12:30:00"]', datetime),
        (dict[Any, str] | dict[Any, UUID], '{"a":"12345678-1234-5678-1234-567812345678"}', str),
        (dict[Any, UUID] | dict[Any, str], '{"a":"12345678-1234-5678-1234-567812345678"}', UUID),
    ],
    ids=[
        'str-uuid',
        'uuid-str',
        'str-date',
        'date-str',
        'str-datetime',
        'datetime-str',
        'dict-str-uuid',
        'dict-uuid-str',
    ],
)
def test_cursor_union_json_string_exactness(schema: Any, data: str, expected: type[Any], strict: bool) -> None:
    adapter = TypeAdapter(schema)
    # Retain ordinary JSON dispatch without converting the values into Python first.
    ordinary = SchemaValidator(core_schema.chain_schema([adapter.core_schema, core_schema.any_schema()]))
    assert 'ChainValidator' in repr(ordinary)
    for validator in (ordinary, adapter):
        result = validator.validate_json(data, strict=strict)
        item = next(iter(result.values())) if isinstance(result, dict) else result[0]
        assert type(item) is expected


@pytest.mark.parametrize(
    'first, second, data, expected',
    [
        (int, float, '[1]', int),
        (int, float, '[1.0]', float),
        (int, float, '[1.5]', float),
        (bool, int, '[true]', bool),
        (bool, int, '[1]', int),
        (bool, float, '[true]', bool),
        (bool, float, '[1.0]', float),
        (str, bool, '["true"]', str),
        (str, int, '["1"]', str),
        (str, float, '["1.5"]', str),
        (TextChoice, str, '["a"]', str),
    ],
)
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('strict', [False, True])
def test_cursor_union_primitive_scoring(
    first: type[Any], second: type[Any], data: str, expected: type[Any], reverse: bool, strict: bool
) -> None:
    schema = list[second] | list[first] if reverse else list[first] | list[second]
    adapter = TypeAdapter(schema)
    ordinary = SchemaValidator(core_schema.chain_schema([adapter.core_schema, core_schema.any_schema()]))
    assert type(ordinary.validate_json(data, strict=strict)[0]) is expected
    assert type(adapter.validate_json(data, strict=strict)[0]) is expected
