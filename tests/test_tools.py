from typing import Dict, List, Mapping

import pytest

from pydantic import BaseModel, ValidationError, dump_as_type, parse_as_type


def test_parse_as_type():
    class ModelA(BaseModel):
        a: Mapping[int, str]

    class ModelB(ModelA):
        b: int

    model_b = ModelB(a={1: 'f'}, b=2)

    parsed = parse_as_type([model_b], List[ModelA])
    assert parsed == [model_b]


def test_dump_as_type():
    class SubmodelA(BaseModel):
        a: int

    class SubmodelB(SubmodelA):
        b: int

    class ModelA(BaseModel):
        int1: int
        a: SubmodelA
        list_a: List[SubmodelA]
        map_a: Dict[str, SubmodelA]

        submodel_list: List[SubmodelA]
        submodel_map: Mapping[int, SubmodelA]

    class ModelB(ModelA):
        int2: int

        b: SubmodelB
        list_b: List[SubmodelB]
        map_b: Dict[str, SubmodelB]

        submodel_list: List[SubmodelB]
        submodel_map: Mapping[int, SubmodelB]

    submodel_a = SubmodelA(a=1)
    submodel_b = SubmodelB(a=1, b=2)

    model_b = ModelB(
        int1=1,
        int2=2,
        a=submodel_a,
        list_a=[submodel_a],
        map_a={'a': submodel_a},
        b=submodel_b,
        list_b=[submodel_b],
        map_b={'b': submodel_b},
        submodel_list=[submodel_b],
        submodel_map={1: submodel_b},
    )

    expected_dumped_model = {
        'a': {'a': 1},
        'int1': 1,
        'list_a': [{'a': 1}],
        'map_a': {'a': {'a': 1}},
        'submodel_list': [{'a': 1}],
        'submodel_map': {1: {'a': 1}},
    }

    dumped_model = dump_as_type(model_b, ModelA)
    assert dumped_model == expected_dumped_model

    dumped_map = dump_as_type({1: model_b}, Dict[int, ModelA])
    assert dumped_map == {1: expected_dumped_model}

    dumped_list = dump_as_type([model_b], List[ModelA])
    assert dumped_list == [expected_dumped_model]


def test_dump_as_type_fails():
    class Model(BaseModel):
        x: int

    class SubModel(BaseModel):
        x: str

    submodel = SubModel(x='a')

    with pytest.raises(ValidationError) as exc_info:
        dump_as_type(submodel, Model)
    assert exc_info.value.errors() == [
        {'loc': ('obj', 'x'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert exc_info.value.model.__name__ == 'ParsingModel[Model] (for dump_as_type)'


def test_parse_as_type_succeeds():
    assert parse_as_type('1', int) == 1


def test_parse_as_type_fails():
    with pytest.raises(ValidationError) as exc_info:
        parse_as_type('a', int)
    assert exc_info.value.errors() == [
        {'loc': ('obj',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert exc_info.value.model.__name__ == 'ParsingModel[int] (for parse_as_type)'
