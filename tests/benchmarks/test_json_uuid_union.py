"""JSON string scoring must preserve UUID selection in smart container unions."""

import json
from uuid import UUID

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter


@pytest.mark.parametrize('order', ['str-first', 'uuid-first'])
def test_json_uuid_union(benchmark: BenchmarkFixture, order: str) -> None:
    values = [f'12345678-1234-5678-1234-{index:012x}' for index in range(1000)]
    data = json.dumps(values).encode()
    annotation = list[str] | list[UUID] if order == 'str-first' else list[UUID] | list[str]
    adapter = TypeAdapter(annotation)
    result = adapter.validate_json(data)
    assert len(result) == len(values)
    assert all(isinstance(value, UUID) for value in result)
    assert [str(value) for value in result] == values
    benchmark(adapter.validate_json, data)
