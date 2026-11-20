"""Discriminator lookup and selected-branch validation on container values."""

import json
from typing import Annotated, Any, Literal

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


class First(BaseModel):
    kind: Literal['first']
    values: list[int]


class Second(BaseModel):
    kind: Literal['second']
    values: list[int]


Tagged = Annotated[First | Second, Field(discriminator='kind')]


@pytest.mark.benchmark(group='JSON tagged union containers')
@pytest.mark.parametrize('case', ['tag-first', 'tag-last', 'small-models', 'invalid-tag', 'invalid-item'])
def test_json_tagged_union_containers(benchmark: BenchmarkFixture, case: str) -> None:
    adapter: TypeAdapter[Any]
    if case == 'small-models':
        adapter = TypeAdapter(list[Tagged])
        data = json.dumps(
            [{'kind': 'first' if i % 2 else 'second', 'values': [i, i + 1]} for i in range(1000)]
        ).encode()
    else:
        adapter = TypeAdapter(Tagged)
        values: list[int | str] = list(range(2000))
        if case == 'invalid-item':
            values[-1] = 'invalid'
        kind = 'invalid' if case == 'invalid-tag' else 'first'
        payload = {'values': values, 'kind': kind} if case == 'tag-last' else {'kind': kind, 'values': values}
        data = json.dumps(payload).encode()

    if case.startswith('invalid'):
        with pytest.raises(ValidationError):
            adapter.validate_json(data)

        def reject() -> None:
            try:
                adapter.validate_json(data)
            except ValidationError:
                pass
            else:
                raise AssertionError('Invalid tagged union value was accepted')

        benchmark(reject)
    else:
        result = adapter.validate_json(data)
        if case == 'small-models':
            assert len(result) == 1000
            assert result[-1].values == [999, 1000]
        else:
            assert result.kind == 'first'
            assert len(result.values) == 2000
        benchmark(adapter.validate_json, data)
