"""Union values that can avoid materializing container subtrees."""

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


@pytest.mark.benchmark(group='JSON union containers')
@pytest.mark.parametrize(
    'case',
    [
        'array-int',
        'array-str',
        'smart-first',
        'smart-last',
        'left-first',
        'left-last',
        'small-models',
        'invalid-array',
        'invalid-model',
    ],
)
def test_json_union_containers(benchmark: BenchmarkFixture, case: str) -> None:
    adapter: TypeAdapter[Any]
    if case.startswith('array') or case == 'invalid-array':
        adapter = TypeAdapter(list[int] | list[str])
        items = list(range(2000)) if case == 'array-int' else [str(i) for i in range(2000)]
        if case == 'invalid-array':
            items = [None]
        data = json.dumps(items).encode()
    elif case == 'small-models':
        adapter = TypeAdapter(list[First | Second])
        data = json.dumps(
            [{'kind': 'first' if i % 2 else 'second', 'values': [i, i + 1]} for i in range(1000)]
        ).encode()
    else:
        mode = 'left_to_right' if case.startswith('left') else 'smart'
        adapter = TypeAdapter(Annotated[First | Second, Field(union_mode=mode)])
        kind = 'first' if case.endswith('first') else 'second'
        if case == 'invalid-model':
            kind = 'neither'
        data = json.dumps({'kind': kind, 'values': list(range(2000))}).encode()

    if case.startswith('invalid'):
        with pytest.raises(ValidationError):
            adapter.validate_json(data)

        def reject() -> None:
            try:
                adapter.validate_json(data)
            except ValidationError:
                pass
            else:
                raise AssertionError('Invalid union value was accepted')

        benchmark(reject)
    else:
        result = adapter.validate_json(data)
        if case.startswith('array'):
            assert len(result) == 2000
            assert type(result[0]) is (int if case == 'array-int' else str)
        elif case == 'small-models':
            assert len(result) == 1000
            assert result[-1].values == [999, 1000]
        else:
            assert result.kind == ('first' if case.endswith('first') else 'second')
            assert len(result.values) == 2000
        benchmark(adapter.validate_json, data)
