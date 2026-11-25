"""Isolate scalar integer conversion from the existing large JSON number arrays."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter, create_model


@pytest.mark.benchmark(group='integer validation')
@pytest.mark.parametrize('shape', ['scalar', 'model'])
@pytest.mark.parametrize('kind', ['i64', 'positive-bigint', 'negative-bigint'])
def test_json_integer_validation(benchmark: BenchmarkFixture, shape: str, kind: str) -> None:
    value = 123456789 if kind == 'i64' else 10**60 + 123456789
    if kind == 'negative-bigint':
        value = -value
    if shape == 'scalar':
        adapter = TypeAdapter(int)
        data = str(value).encode()
        assert adapter.validate_json(data) == value
        benchmark(adapter.validate_json, data)
    else:
        model = create_model('IntegerRecord', **{f'value_{i}': (int, ...) for i in range(8)})
        expected = {f'value_{i}': value for i in range(8)}
        data = json.dumps(expected).encode()
        assert model.model_validate_json(data).model_dump() == expected
        benchmark(model.model_validate_json, data)


@pytest.mark.benchmark(group='integer validation')
@pytest.mark.parametrize('annotation', [int, int | str], ids=['int', 'int-or-str'])
def test_python_integer_validation(benchmark: BenchmarkFixture, annotation: object) -> None:
    adapter = TypeAdapter(annotation)
    value = 123456789
    assert adapter.validate_python(value) == value
    benchmark(adapter.validate_python, value)
