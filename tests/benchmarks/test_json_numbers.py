"""Separate number shapes following jiter's short/roundtrip/long-float and integer cases.

Build the JSON tokens directly: serializing Python floats would round away the long
significands before they reach the parser. No random data or external corpus is required.
"""

import pytest
from pydantic_core import from_json
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter


@pytest.mark.parametrize('shape', ['short-decimal', 'roundtrip-double', 'long-significand', 'big-integer'])
@pytest.mark.parametrize('api', ['from_json', 'validate_json'])
def test_json_number_shapes(benchmark: BenchmarkFixture, shape: str, api: str) -> None:
    expected: list[int] | list[float]
    if shape == 'big-integer':
        # These exceed 64-bit integers and must become arbitrary-precision Python ints.
        tokens = [str((-1) ** i * (10**60 + i)) for i in range(256)]
        expected = [int(token) for token in tokens]
        adapter = TypeAdapter(list[int])
    else:
        if shape == 'short-decimal':
            tokens = [f'{i}.125' for i in range(256)]
        elif shape == 'roundtrip-double':
            tokens = [format((i + 1) / 257, '.17g') for i in range(256)]
        else:
            tokens = [f'{i}.123456789012345678901234567890123456789' for i in range(256)]
        expected = [float(token) for token in tokens]
        adapter = TypeAdapter(list[float])
    data = ('[' + ','.join(tokens) + ']').encode()
    if api == 'from_json':
        assert from_json(data) == expected
        benchmark(from_json, data)
    else:
        assert adapter.validate_json(data) == expected
        benchmark(adapter.validate_json, data)
