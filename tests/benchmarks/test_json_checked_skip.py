"""Measure checked skips separately for bytes and already decoded Python strings."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel


class IgnoredFields(BaseModel):
    value: int


class DeferredFields(BaseModel):
    first: int
    payload: list[str]


@pytest.mark.benchmark(group='JSON checked skips')
@pytest.mark.parametrize('mode', ['bytes', 'str'])
@pytest.mark.parametrize('case', ['ignored', 'deferred'])
def test_json_checked_skips(benchmark: BenchmarkFixture, mode: str, case: str) -> None:
    text = '日本語 café Ελληνικά'
    if case == 'ignored':
        model = IgnoredFields
        document = {'value': 1, **{f'extra_{i}': text * 4 for i in range(256)}}
    else:
        model = DeferredFields
        document = {'payload': [text * 4] * 256, 'first': 1}
    encoded = json.dumps(document, ensure_ascii=False)
    data = encoded.encode() if mode == 'bytes' else encoded
    result = model.model_validate_json(data)
    if case == 'ignored':
        assert result.value == 1
    else:
        assert result.first == 1
        assert result.payload == document['payload']
    benchmark(model.model_validate_json, data)


@pytest.mark.benchmark(group='JSON checked skips')
@pytest.mark.parametrize('metadata', ['ascii', '日本語'])
def test_json_scalar_skip_before_known_payload(benchmark: BenchmarkFixture, metadata: str) -> None:
    class Payload(BaseModel):
        values: list[str]

    values = ['日本語 café Ελληνικά' * 4] * 256
    data = json.dumps({'metadata': metadata, 'values': values}, ensure_ascii=False).encode()
    assert Payload.model_validate_json(data).values == values
    benchmark(Payload.model_validate_json, data)
