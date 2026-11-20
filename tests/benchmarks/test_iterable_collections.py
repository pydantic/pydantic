"""Collection validation from sized and unknown-length Python iterables."""

from collections import deque

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter


@pytest.mark.benchmark(group='iterable collection validation')
@pytest.mark.parametrize('length', [2, 9, 1000])
def test_untyped_deque_from_tuple(benchmark: BenchmarkFixture, length: int) -> None:
    adapter = TypeAdapter(deque)
    data = tuple(range(length))
    assert adapter.validate_python(data) == deque(data)
    benchmark(adapter.validate_python, data)


@pytest.mark.benchmark(group='iterable collection validation')
@pytest.mark.parametrize('length', [2, 9, 1000])
def test_typed_list_from_generator(benchmark: BenchmarkFixture, length: int) -> None:
    adapter = TypeAdapter(list[int])
    data = tuple(range(length))

    def validate() -> list[int]:
        # A generator has no length hint and must be recreated for each validation.
        return adapter.validate_python(value for value in data)

    assert validate() == list(data)
    benchmark(validate)
