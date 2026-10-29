"""Compare steady-state JSON string caching for repeated and unique short values.

Inspired by jiter's string_array and string_array_unique benchmarks. Object keys repeat in
both workloads, so the keys-only mode distinguishes key caching from value caching.
"""

import json
from typing import Literal

import pytest
from pydantic_core import from_json
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import ConfigDict, TypeAdapter


@pytest.mark.parametrize('unique', [False, True], ids=['repeated', 'unique'])
@pytest.mark.parametrize('cache_strings', ['all', 'keys', 'none'])
@pytest.mark.parametrize('api', ['from_json', 'validate_json'])
def test_json_string_cache(
    benchmark: BenchmarkFixture,
    unique: bool,
    cache_strings: Literal['all', 'keys', 'none'],
    api: str,
) -> None:
    expected = [{'name': f'user-{i:04d}' if unique else 'user-0000', 'role': 'reader'} for i in range(256)]
    data = json.dumps(expected).encode()
    if api == 'from_json':
        assert from_json(data, cache_strings=cache_strings) == expected
        benchmark(from_json, data, cache_strings=cache_strings)
    else:
        adapter = TypeAdapter(list[dict[str, str]], config=ConfigDict(cache_strings=cache_strings))
        assert adapter.validate_json(data) == expected
        benchmark(adapter.validate_json, data)
