"""Valid and fallback JSON inputs for a model containing simple nested models."""

import json

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic_core import SchemaValidator, ValidationError, core_schema


@pytest.fixture(scope='module')
def nested_model_json() -> tuple[SchemaValidator, bytes, bytes, bytes]:
    class Inner:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    class Outer:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    inner = core_schema.model_schema(
        Inner,
        core_schema.model_fields_schema(
            fields={
                'i': core_schema.model_field(core_schema.int_schema()),
                's': core_schema.model_field(core_schema.str_schema()),
            }
        ),
    )
    outer = core_schema.model_schema(
        Outer,
        core_schema.model_fields_schema(fields={'items': core_schema.model_field(core_schema.list_schema(inner))}),
    )
    validator = SchemaValidator(outer)

    items = [{'i': i, 's': str(i)} for i in range(100)]
    valid = json.dumps({'items': items}).encode()
    items[-1]['i'] = 'bad'
    type_error = json.dumps({'items': items}).encode()
    trailing_json = valid + b' trailing'
    return validator, valid, type_error, trailing_json


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_valid_json(
    benchmark: BenchmarkFixture, nested_model_json: tuple[SchemaValidator, bytes, bytes, bytes]
) -> None:
    validator, valid, _, _ = nested_model_json
    result = validator.validate_json(valid)
    assert len(result.items) == 100
    benchmark(validator.validate_json, valid)


def _reject(validator: SchemaValidator, data: bytes) -> None:
    try:
        validator.validate_json(data)
    except ValidationError:
        pass
    else:
        raise AssertionError('Invalid JSON input was accepted')


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_late_type_error(
    benchmark: BenchmarkFixture, nested_model_json: tuple[SchemaValidator, bytes, bytes, bytes]
) -> None:
    validator, _, type_error, _ = nested_model_json
    _reject(validator, type_error)
    benchmark(_reject, validator, type_error)


@pytest.mark.benchmark(group='nested JSON model')
def test_nested_model_trailing_json(
    benchmark: BenchmarkFixture, nested_model_json: tuple[SchemaValidator, bytes, bytes, bytes]
) -> None:
    validator, _, _, trailing_json = nested_model_json
    _reject(validator, trailing_json)
    benchmark(_reject, validator, trailing_json)
