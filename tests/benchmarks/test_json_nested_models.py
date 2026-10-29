"""Valid and fallback JSON inputs for a model containing simple nested models."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, ValidationError


class Inner(BaseModel):
    i: int
    s: str


class Outer(BaseModel):
    items: list[Inner]


@pytest.fixture(scope='module')
def nested_model_json() -> tuple[bytes, bytes, bytes]:
    items = [{'i': i, 's': str(i)} for i in range(100)]
    valid = json.dumps({'items': items}).encode()
    items[-1]['i'] = 'bad'
    type_error = json.dumps({'items': items}).encode()
    trailing_json = valid + b' trailing'
    return valid, type_error, trailing_json


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_valid_json(benchmark: BenchmarkFixture, nested_model_json: tuple[bytes, bytes, bytes]) -> None:
    valid, _, _ = nested_model_json
    result = Outer.model_validate_json(valid)
    assert len(result.items) == 100
    benchmark(Outer.model_validate_json, valid)


def _reject(data: bytes) -> None:
    try:
        Outer.model_validate_json(data)
    except ValidationError:
        pass
    else:
        raise AssertionError('Invalid JSON input was accepted')


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_late_type_error(
    benchmark: BenchmarkFixture, nested_model_json: tuple[bytes, bytes, bytes]
) -> None:
    _, type_error, _ = nested_model_json
    _reject(type_error)
    benchmark(_reject, type_error)


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_trailing_json(benchmark: BenchmarkFixture, nested_model_json: tuple[bytes, bytes, bytes]) -> None:
    _, _, trailing_json = nested_model_json
    _reject(trailing_json)
    benchmark(_reject, trailing_json)
