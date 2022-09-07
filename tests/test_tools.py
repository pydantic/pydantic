import json
from typing import Dict, List, Mapping, Union

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.dataclasses import dataclass
from pydantic.tools import parse_file_as, parse_obj_as, parse_raw_as, schema_json_of, schema_of


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
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert exc_info.value.model.__name__ == 'ParsingModel[int]'


def test_parsing_model_naming():
    with pytest.raises(ValidationError) as exc_info:
        parse_obj_as(int, 'a')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for ParsingModel[int]'

    with pytest.raises(ValidationError) as exc_info:
        parse_obj_as(int, 'a', type_name='ParsingModel')
    assert str(exc_info.value).split('\n')[0] == '1 validation error for ParsingModel'

    with pytest.raises(ValidationError) as exc_info:
        parse_obj_as(int, 'a', type_name=lambda type_: type_.__name__)
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


def test_parse_file_as(tmp_path):
    p = tmp_path / 'test.json'
    p.write_text('{"1": "2"}')
    assert parse_file_as(Dict[int, int], p) == {1: 2}


def test_parse_file_as_json_loads(tmp_path):
    def custom_json_loads(*args, **kwargs):
        data = json.loads(*args, **kwargs)
        data[1] = 99
        return data

    p = tmp_path / 'test_json_loads.json'
    p.write_text('{"1": "2"}')
    assert parse_file_as(Dict[int, int], p, json_loads=custom_json_loads) == {1: 99}


def test_raw_as():
    class Item(BaseModel):
        id: int
        name: str

    item_data = '[{"id": 1, "name": "My Item"}]'
    items = parse_raw_as(List[Item], item_data)
    assert items == [Item(id=1, name='My Item')]


def test_schema():
    assert schema_of(Union[int, str], title='IntOrStr') == {
        'title': 'IntOrStr',
        'anyOf': [{'type': 'integer'}, {'type': 'string'}],
    }
    assert schema_json_of(Union[int, str], title='IntOrStr', indent=2) == (
        '{\n'
        '  "title": "IntOrStr",\n'
        '  "anyOf": [\n'
        '    {\n'
        '      "type": "integer"\n'
        '    },\n'
        '    {\n'
        '      "type": "string"\n'
        '    }\n'
        '  ]\n'
        '}'
    )
