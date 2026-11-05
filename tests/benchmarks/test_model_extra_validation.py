import json

import pytest

from pydantic import BaseModel, ConfigDict, ValidationError

pytestmark = [
    pytest.mark.benchmark(group='model_extra_validation'),
    pytest.mark.parametrize('mode', ['python', 'json']),
]

DATA = {'field1': 'test', 'field2': 42, **{f'extra_field_{i}': i for i in range(100)}}
JSON_DATA = json.dumps(DATA)


class ExtraModel(BaseModel):
    model_config = ConfigDict(extra='allow')

    field1: str
    field2: int


class TypedExtraModel(BaseModel):
    model_config = ConfigDict(extra='allow')

    __pydantic_extra__: dict[str, int]

    field1: str
    field2: int


class ForbidExtraModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    field1: str
    field2: int


def _bench(benchmark, model: type[BaseModel], mode: str) -> None:
    if mode == 'python':
        benchmark(model.model_validate, DATA)
    else:
        benchmark(model.model_validate_json, JSON_DATA)


def test_extra_allow_validation(mode: str, benchmark):
    _bench(benchmark, ExtraModel, mode)


def test_typed_extra_allow_validation(mode: str, benchmark):
    _bench(benchmark, TypedExtraModel, mode)


def test_extra_forbid_validation(mode: str, benchmark):
    def validate(model_validate, data):
        try:
            model_validate(data)
        except ValidationError:
            pass

    if mode == 'python':
        benchmark(validate, ForbidExtraModel.model_validate, DATA)
    else:
        benchmark(validate, ForbidExtraModel.model_validate_json, JSON_DATA)
