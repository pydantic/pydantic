"""Compare successful cursor lists with early and late item validation errors."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter, ValidationError


@pytest.mark.benchmark(group='JSON list item errors')
@pytest.mark.parametrize('case', ['valid', 'invalid-first', 'invalid-last'])
def test_json_list_item_errors(benchmark: BenchmarkFixture, case: str) -> None:
    adapter = TypeAdapter(list[int])
    items: list[int | str] = list(range(10000))
    if case != 'valid':
        items[0 if case == 'invalid-first' else -1] = 'bad'
    data = json.dumps(items).encode()
    if case == 'valid':
        assert adapter.validate_json(data) == list(range(10000))
        benchmark(adapter.validate_json, data)
        return

    with pytest.raises(ValidationError) as expected:
        adapter.validate_json(data)
    assert [error['loc'] for error in expected.value.errors()] == [(0 if case == 'invalid-first' else 9999,)]

    def reject() -> None:
        try:
            adapter.validate_json(data)
        except ValidationError:
            pass
        else:
            raise AssertionError('Invalid list item was accepted')

    benchmark(reject)
