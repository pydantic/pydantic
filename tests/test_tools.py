from typing import Dict, List, Mapping

import pytest

from pydantic import BaseModel, ValidationError, parse_obj
from pydantic.dataclasses import dataclass
from pydantic.tools import parse_file


class Model(BaseModel):
    x: int
    y: bool
    z: str


model_inputs = {'x': '1', 'y': 'true', 'z': 'abc'}
model = Model(**model_inputs)


@pytest.mark.parametrize('obj,type_,parsed', [('1', int, 1), (['1'], List[int], [1]), (model_inputs, Model, model)])
def test_parse_obj(obj, type_, parsed):
    assert parse_obj(type_, obj) == parsed


def test_parse_obj_preserves_subclasses():
    class ModelA(BaseModel):
        a: Mapping[int, str]

    class ModelB(ModelA):
        b: int

    model_b = ModelB(a={1: 'f'}, b=2)

    parsed = parse_obj(List[ModelA], [model_b])
    assert parsed == [model_b]


def test_parse_obj_fails():
    with pytest.raises(ValidationError) as exc_info:
        parse_obj(int, 'a')
    assert exc_info.value.errors() == [
        {'loc': ('obj',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert exc_info.value.model.__name__ == 'ParsingModel[int]'


def test_parsing_model_naming():
    with pytest.raises(ValidationError) as exc_info:
        parse_obj(int, 'a')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for ParsingModel[int]'

    with pytest.raises(ValidationError) as exc_info:
        parse_obj(int, 'a', type_name='ParsingModel')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for ParsingModel'

    with pytest.raises(ValidationError) as exc_info:
        parse_obj(int, 'a', type_name=lambda type_: type_.__name__)
    assert str(exc_info.value).split('\n')[0] == '1 validation error for int'


def test_parse_as_dataclass():
    @dataclass
    class PydanticDataclass:
        x: int

    inputs = {'x': '1'}
    assert parse_obj(PydanticDataclass, inputs) == PydanticDataclass(1)


def test_parse_as_mapping():
    inputs = {'1': '2'}
    assert parse_obj(Dict[int, int], inputs) == {1: 2}


def test_parse_file(tmpdir):
    p = tmpdir.join('test.json')
    p.write('{"1": "2"}')
    assert parse_file(Dict[int, int], str(p)) == {1: 2}
