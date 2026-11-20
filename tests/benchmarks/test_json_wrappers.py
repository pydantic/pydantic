"""Container-valued after validators, from tiny overhead to large payloads."""

import json
from typing import Annotated

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import AfterValidator, BaseModel, TypeAdapter


def identity(value: list[int]) -> list[int]:
    return value


class WrappedModel(BaseModel):
    values: Annotated[list[int], AfterValidator(identity)]


@pytest.mark.parametrize('size', [2, 10000])
@pytest.mark.parametrize('nested', [False, True])
def test_json_after_containers(benchmark: BenchmarkFixture, size: int, nested: bool) -> None:
    values = list(range(size))
    adapter = TypeAdapter(WrappedModel if nested else Annotated[list[int], AfterValidator(identity)])
    data = json.dumps({'values': values} if nested else values).encode()
    result = adapter.validate_json(data)
    assert (result.values if nested else result) == values
    benchmark(adapter.validate_json, data)
