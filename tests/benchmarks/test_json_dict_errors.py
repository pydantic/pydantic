"""Measure complete JSON dictionary traversal inside a model."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, ValidationError


class DictModel(BaseModel):
    values: dict[str, int]


@pytest.mark.benchmark(group='JSON dictionary item errors')
@pytest.mark.parametrize('case', ['valid', 'invalid-first', 'invalid-last'])
def test_json_dict_item_errors(benchmark: BenchmarkFixture, case: str) -> None:
    items: dict[str, int | str] = {f'item_{index}': index for index in range(10000)}
    invalid_key = 'item_0' if case == 'invalid-first' else 'item_9999'
    if case != 'valid':
        items[invalid_key] = 'bad'
    data = json.dumps({'values': items}).encode()
    if case == 'valid':
        assert DictModel.model_validate_json(data).values == items
        benchmark(DictModel.model_validate_json, data)
        return

    with pytest.raises(ValidationError) as expected:
        DictModel.model_validate_json(data)
    assert [error['loc'] for error in expected.value.errors()] == [('values', invalid_key)]

    def reject() -> None:
        try:
            DictModel.model_validate_json(data)
        except ValidationError:
            pass
        else:
            raise AssertionError('Invalid dictionary item was accepted')

    benchmark(reject)
