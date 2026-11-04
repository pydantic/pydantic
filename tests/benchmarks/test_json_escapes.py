"""Benchmarks covering escaping when serializing large strings."""

import base64
import json
from typing import Literal

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel


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
