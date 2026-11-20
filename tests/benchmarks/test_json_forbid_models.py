"""Valid forbidden-extra models at the root and inside a typed batch."""

import json

from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, ConfigDict, TypeAdapter


class ForbidListModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    values: list[int]


class ForbidRow(BaseModel):
    model_config = ConfigDict(extra='forbid')

    i: int
    s: str


def test_json_forbid_model_large_list(benchmark: BenchmarkFixture) -> None:
    values = list(range(10000))
    data = json.dumps({'values': values}).encode()
    assert ForbidListModel.model_validate_json(data).values == values
    benchmark(ForbidListModel.model_validate_json, data)


def test_json_forbid_model_batch(benchmark: BenchmarkFixture) -> None:
    adapter = TypeAdapter(list[ForbidRow])
    values = [{'i': index, 's': str(index)} for index in range(1000)]
    data = json.dumps(values).encode()
    assert [row.model_dump() for row in adapter.validate_json(data)] == values
    benchmark(adapter.validate_json, data)
