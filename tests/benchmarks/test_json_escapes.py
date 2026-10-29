"""Hold decoded text constant while exercising JSON's literal and escape paths.

Complements the non-ASCII and escapes groups in jiter's json-cases benchmarks.
"""

import json

import pytest
from pydantic_core import from_json
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter


@pytest.mark.parametrize('ensure_ascii', [False, True], ids=['utf8', 'unicode-escapes'])
@pytest.mark.parametrize('api', ['from_json', 'validate_json'])
def test_json_unicode_encoding(benchmark: BenchmarkFixture, ensure_ascii: bool, api: str) -> None:
    expected = ['日本語 한국어 Ελληνικά العربية café 😀' for _ in range(128)]
    data = json.dumps(expected, ensure_ascii=ensure_ascii).encode()
    # Bypass string caching so repeated values still exercise decoding and allocation.
    if api == 'from_json':
        assert from_json(data, cache_strings=False) == expected
        benchmark(from_json, data, cache_strings=False)
    else:
        adapter = TypeAdapter(list[str], config={'cache_strings': False})
        assert adapter.validate_json(data) == expected
        benchmark(adapter.validate_json, data)
