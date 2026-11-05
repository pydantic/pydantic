"""Hold decoded text constant while exercising JSON's literal and escape paths.

Complements the non-ASCII and escapes groups in jiter's json-cases benchmarks.
Also covers escaping when serializing large strings.
"""

import base64
import json
from typing import Literal

import pytest
from pydantic_core import from_json
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, TypeAdapter


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


class Payload(BaseModel):
    kind: Literal['data']
    buffer: str


DUMP_PAYLOADS = {
    'base64': base64.b64encode(bytes(range(256)) * 300).decode(),
    # JSON stored in a string field (e.g. LLM tool call arguments): a `"` every few bytes.
    'nested-json': json.dumps([{'id': i, 'name': f'item {i}', 'tags': ['a', 'b']} for i in range(2000)]),
    # Prose: a few quotes and newlines per line.
    'text': 'He said "hello" and left.\nThen nothing happened for a while, until the next line.\n' * 1200,
}


@pytest.mark.parametrize('payload', DUMP_PAYLOADS.values(), ids=DUMP_PAYLOADS.keys())
def test_json_dump_large_string(benchmark: BenchmarkFixture, payload: str) -> None:
    model = Payload(kind='data', buffer=payload)
    assert json.loads(model.model_dump_json())['buffer'] == payload
    benchmark(model.model_dump_json)
