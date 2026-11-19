"""Successful validation at the upper bound of scalar and model list fields."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import Field, create_model


@pytest.mark.benchmark(group='JSON bounded lists')
@pytest.mark.parametrize('items', ['integers', 'models'])
def test_json_bounded_list_field(benchmark: BenchmarkFixture, items: str) -> None:
    if items == 'integers':
        annotation = list[int]
        values = list(range(10000))
    else:
        item = create_model('Item', i=(int, ...), s=(str, ...))
        annotation = list[item]
        values = [{'i': i, 's': str(i)} for i in range(1000)]
    model = create_model('BoundedList', values=(annotation, Field(max_length=len(values))))
    expected = {'values': values}
    data = json.dumps(expected).encode()
    assert model.model_validate_json(data).model_dump() == expected
    benchmark(model.model_validate_json, data)
