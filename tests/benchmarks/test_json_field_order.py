"""Compare equivalent model JSON documents with different object key orders."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import create_model


@pytest.mark.benchmark(group='JSON field order')
@pytest.mark.parametrize('order', ['schema', 'reverse', 'container-first'])
def test_json_field_order(benchmark: BenchmarkFixture, order: str) -> None:
    model = create_model('Record', count=(int, ...), name=(str, ...), values=(list[int], ...), ratio=(float, ...))
    expected = {'count': 123, 'name': 'hello', 'values': list(range(256)), 'ratio': 1.5}
    keys = list(expected)
    if order == 'reverse':
        keys.reverse()
    elif order == 'container-first':
        keys = ['values', 'count', 'name', 'ratio']
    data = json.dumps({key: expected[key] for key in keys}).encode()
    assert model.model_validate_json(data).model_dump() == expected
    benchmark(model.model_validate_json, data)
