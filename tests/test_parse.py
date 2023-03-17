from typing import List, Tuple

import pytest

from pydantic import BaseModel, ValidationError, parse_obj_as


class Model(BaseModel):
    a: float
    b: int = 10


def test_obj():
    m = Model.model_validate(dict(a=10.2))
    assert str(m) == 'a=10.2 b=10'


def test_model_validate_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate([1, 2, 3])
    assert exc_info.value.errors() == [
        {'input': [1, 2, 3], 'loc': (), 'msg': 'Input should be a valid dictionary', 'type': 'dict_type'}
    ]


@pytest.mark.xfail(reason='working on V2')
def test_model_validate_submodel():
    m = Model.model_validate(Model(a=10.2))
    assert m.model_dump() == {'a': 10.2, 'b': 10}


@pytest.mark.xfail(reason='working on V2')
def test_model_validate_wrong_model():
    class Foo(BaseModel):
        c = 123

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate(Foo())
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


@pytest.mark.xfail(reason='working on V2')
def test_model_validate_root():
    class MyModel(BaseModel):
        __root__: str

    m = MyModel.model_validate('a')
    assert m.model_dump() == {'__root__': 'a'}
    assert m.__root__ == 'a'


@pytest.mark.xfail(reason='working on V2')
def test_parse_root_list():
    class MyModel(BaseModel):
        __root__: List[str]

    m = MyModel.model_validate(['a'])
    assert m.model_dump() == {'__root__': ['a']}
    assert m.__root__ == ['a']


@pytest.mark.xfail(reason='working on V2')
def test_parse_nested_root_list():
    class NestedData(BaseModel):
        id: str

    class NestedModel(BaseModel):
        __root__: List[NestedData]

    class MyModel(BaseModel):
        nested: NestedModel

    m = MyModel.model_validate({'nested': [{'id': 'foo'}]})
    assert isinstance(m.nested, NestedModel)
    assert isinstance(m.nested.__root__[0], NestedData)


@pytest.mark.xfail(reason='working on V2')
def test_parse_nested_root_tuple():
    class NestedData(BaseModel):
        id: str

    class NestedModel(BaseModel):
        __root__: Tuple[int, NestedData]

    class MyModel(BaseModel):
        nested: List[NestedModel]

    data = [0, {'id': 'foo'}]
    m = MyModel.model_validate({'nested': [data]})
    assert isinstance(m.nested[0], NestedModel)
    assert isinstance(m.nested[0].__root__[1], NestedData)

    nested = parse_obj_as(NestedModel, data)
    assert isinstance(nested, NestedModel)


@pytest.mark.xfail(reason='working on V2')
def test_parse_nested_custom_root():
    class NestedModel(BaseModel):
        __root__: List[str]

    class MyModel(BaseModel):
        __root__: NestedModel

    nested = ['foo', 'bar']
    m = MyModel.model_validate(nested)
    assert isinstance(m, MyModel)
    assert isinstance(m.__root__, NestedModel)
    assert isinstance(m.__root__.__root__, List)
    assert isinstance(m.__root__.__root__[0], str)


def test_json():
    assert Model.model_validate_json('{"a": 12, "b": 8}') == Model(a=12, b=8)
