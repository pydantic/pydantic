from typing import List, Mapping

import pytest

from pydantic import BaseModel, ValidationError, parse_as_type


class Model(BaseModel):
    x: int
    y: bool
    z: str


model_inputs = {'x': '1', 'y': 'true', 'z': 'abc'}
model = Model(**model_inputs)


@pytest.mark.parametrize('obj,type_,parsed', [('1', int, 1), (['1'], List[int], [1]), (model_inputs, Model, model)])
def test_parse_as_type(obj, type_, parsed):
    assert parse_as_type(obj, type_) == parsed


def test_parse_as_type_preserves_subclasses():
    class ModelA(BaseModel):
        a: Mapping[int, str]

    class ModelB(ModelA):
        b: int

    model_b = ModelB(a={1: 'f'}, b=2)

    parsed = parse_as_type([model_b], List[ModelA])
    assert parsed == [model_b]


def test_parse_as_type_fails():
    with pytest.raises(ValidationError) as exc_info:
        parse_as_type('a', int)
    assert exc_info.value.errors() == [
        {'loc': ('obj',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert exc_info.value.model.__name__ == 'ParsingModel[int]'


def test_parsing_model_naming():
    with pytest.raises(ValidationError) as exc_info:
        parse_as_type("a", int)
    assert str(exc_info.value).split('\n')[0] == '1 validation error for ParsingModel[int]'

    with pytest.raises(ValidationError) as exc_info:
        parse_as_type("a", int, type_name="ParsingModel")
    assert str(exc_info.value).split('\n')[0] == "1 validation error for ParsingModel"

    with pytest.raises(ValidationError) as exc_info:
        parse_as_type("a", int, type_name=lambda type_: type_.__name__)
    assert str(exc_info.value).split('\n')[0] == "1 validation error for int"
