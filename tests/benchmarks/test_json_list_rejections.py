"""Measure complete list bounds and early fail-fast errors inside a model."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import Field, ValidationError, create_model


@pytest.mark.benchmark(group='JSON list rejections')
@pytest.mark.parametrize('case', ['max-overflow', 'min-short', 'fail-fast'])
def test_json_list_rejections(benchmark: BenchmarkFixture, case: str) -> None:
    values: list[int | str] = list(range(10000))
    if case == 'max-overflow':
        constraint = Field(max_length=9999)
        error_type = 'too_long'
    elif case == 'min-short':
        constraint = Field(min_length=10001)
        error_type = 'too_short'
    else:
        constraint = Field(fail_fast=True)
        error_type = 'int_parsing'
        values[0] = 'bad'
    model = create_model('RejectedList', values=(list[int], constraint))
    data = json.dumps({'values': values}).encode()
    with pytest.raises(ValidationError) as expected:
        model.model_validate_json(data)
    assert expected.value.errors()[0]['type'] == error_type

    def reject() -> None:
        try:
            model.model_validate_json(data)
        except ValidationError:
            pass
        else:
            raise AssertionError('Invalid list was accepted')

    benchmark(reject)
