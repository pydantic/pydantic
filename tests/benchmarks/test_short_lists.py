"""Cover small typed lists separately from the existing thousand-element cases."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter


@pytest.mark.benchmark(group='short list validation')
@pytest.mark.parametrize('mode', ['python', 'json'])
@pytest.mark.parametrize(
    'item_type,length',
    [(int, 0), (int, 1), (int, 2), (int, 8), (int, 9), (float, 2), (float, 9), (str, 2), (str, 9)],
    ids=['int-empty', 'int-one', 'int-two', 'int-eight', 'int-nine', 'float-two', 'float-nine', 'str-two', 'str-nine'],
)
def test_short_typed_lists(
    benchmark: BenchmarkFixture, mode: str, item_type: type[int] | type[float] | type[str], length: int
) -> None:
    adapter = TypeAdapter(list[item_type])
    expected = [item_type(i) for i in range(length)]
    if mode == 'python':
        assert adapter.validate_python(expected) == expected
        benchmark(adapter.validate_python, expected)
    else:
        data = json.dumps(expected).encode()
        assert adapter.validate_json(data) == expected
        benchmark(adapter.validate_json, data)


@pytest.mark.benchmark(group='short list validation')
@pytest.mark.parametrize('mode', ['python', 'json'])
def test_coordinate_pairs(benchmark: BenchmarkFixture, mode: str) -> None:
    adapter = TypeAdapter(list[list[float]])
    expected = [[i + 0.125, i + 0.625] for i in range(256)]
    if mode == 'python':
        assert adapter.validate_python(expected) == expected
        benchmark(adapter.validate_python, expected)
    else:
        data = json.dumps(expected).encode()
        assert adapter.validate_json(data) == expected
        benchmark(adapter.validate_json, data)
