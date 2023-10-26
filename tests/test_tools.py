from typing import Dict, List, Mapping, Union

import pytest

from pydantic import BaseModel, PydanticDeprecatedSince20, ValidationError
from pydantic.dataclasses import dataclass
from pydantic.deprecated.tools import parse_obj_as, schema_json_of, schema_of

pytestmark = pytest.mark.filterwarnings('ignore::DeprecationWarning')


@pytest.mark.parametrize('obj,type_,parsed', [('1', int, 1), (['1'], List[int], [1])])
def test_parse_obj(obj, type_, parsed):
    assert parse_obj_as(type_, obj) == parsed


def test_parse_obj_as_model():
    class Model(BaseModel):
        x: int
        y: bool
        z: str

    model_inputs = {'x': '1', 'y': 'true', 'z': 'abc'}
    assert parse_obj_as(Model, model_inputs) == Model(**model_inputs)


def test_parse_obj_preserves_subclasses():
    class ModelA(BaseModel):
        a: Mapping[int, str]

    class ModelB(ModelA):
        b: int

    model_b = ModelB(a={1: 'f'}, b=2)

    parsed = parse_obj_as(List[ModelA], [model_b])
    assert parsed == [model_b]


def test_parse_obj_fails():
    with pytest.raises(ValidationError) as exc_info:
        parse_obj_as(int, 'a')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_parsing_model_naming():
    with pytest.raises(ValidationError) as exc_info:
        parse_obj_as(int, 'a')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for int'

    with pytest.raises(ValidationError) as exc_info:
        with pytest.warns(PydanticDeprecatedSince20, match='The type_name parameter is deprecated'):
            parse_obj_as(int, 'a', type_name='ParsingModel')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for int'


def test_parse_as_dataclass():
    @dataclass
    class PydanticDataclass:
        x: int

    inputs = {'x': '1'}
    assert parse_obj_as(PydanticDataclass, inputs) == PydanticDataclass(1)


def test_parse_mapping_as():
    inputs = {'1': '2'}
    assert parse_obj_as(Dict[int, int], inputs) == {1: 2}


def test_schema():
    assert schema_of(Union[int, str], title='IntOrStr') == {
        'title': 'IntOrStr',
        'anyOf': [{'type': 'integer'}, {'type': 'string'}],
    }
    assert schema_json_of(Union[int, str], title='IntOrStr', indent=2) == (
        '{\n'
        '  "anyOf": [\n'
        '    {\n'
        '      "type": "integer"\n'
        '    },\n'
        '    {\n'
        '      "type": "string"\n'
        '    }\n'
        '  ],\n'
        '  "title": "IntOrStr"\n'
        '}'
    )
