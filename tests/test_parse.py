import json
import pickle

import pytest

from pydantic import BaseModel, ConfigDict, Field, ValidationError, parse_obj_as


class Model(BaseModel):
    a: float
    b: int = 10


def test_obj():
    m = Model.model_validate(dict(a=10.2))
    assert str(m) == 'a=10.2 b=10'


@pytest.mark.xfail(reason='working on V2')
def test_model_validate_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate([1, 2, 3])
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'Model expected dict not list', 'type': 'type_error'}
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
        __root__: list[str]

    m = MyModel.model_validate(['a'])
    assert m.model_dump() == {'__root__': ['a']}
    assert m.__root__ == ['a']


@pytest.mark.xfail(reason='working on V2')
def test_parse_nested_root_list():
    class NestedData(BaseModel):
        id: str

    class NestedModel(BaseModel):
        __root__: list[NestedData]

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
        __root__: tuple[int, NestedData]

    class MyModel(BaseModel):
        nested: list[NestedModel]

    data = [0, {'id': 'foo'}]
    m = MyModel.model_validate({'nested': [data]})
    assert isinstance(m.nested[0], NestedModel)
    assert isinstance(m.nested[0].__root__[1], NestedData)

    nested = parse_obj_as(NestedModel, data)
    assert isinstance(nested, NestedModel)


@pytest.mark.xfail(reason='working on V2')
def test_parse_nested_custom_root():
    class NestedModel(BaseModel):
        __root__: list[str]

    class MyModel(BaseModel):
        __root__: NestedModel

    nested = ['foo', 'bar']
    m = MyModel.model_validate(nested)
    assert isinstance(m, MyModel)
    assert isinstance(m.__root__, NestedModel)
    assert isinstance(m.__root__.__root__, list)
    assert isinstance(m.__root__.__root__[0], str)


@pytest.mark.xfail(reason='working on V2')
def test_json():
    assert Model.parse_raw('{"a": 12, "b": 8}') == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_json_ct():
    assert Model.parse_raw('{"a": 12, "b": 8}', content_type='application/json') == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_pickle_ct():
    data = pickle.dumps(dict(a=12, b=8))
    assert Model.parse_raw(data, content_type='application/pickle', allow_pickle=True) == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_bad_ct():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', content_type='application/missing')
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'Unknown content-type: application/missing', 'type': 'type_error'}
    ]


@pytest.mark.xfail(reason='working on V2')
def test_bad_proto():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', proto='foobar')
    assert exc_info.value.errors() == [{'loc': ('__root__',), 'msg': 'Unknown protocol: foobar', 'type': 'type_error'}]


@pytest.mark.xfail(reason='working on V2')
def test_file_json(tmpdir):
    p = tmpdir.join('test.json')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_file_json_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_file_json_loads(tmp_path):
    def custom_json_loads(*args, **kwargs):
        data = json.loads(*args, **kwargs)
        data['a'] = 99
        return data

    class Example(BaseModel):
        model_config = ConfigDict(json_loads=custom_json_loads)
        a: int

    p = tmp_path / 'test_json_loads.json'
    p.write_text('{"a": 12}')

    assert Example.parse_file(p) == Example(a=99)


@pytest.mark.xfail(reason='working on V2')
def test_file_pickle(tmpdir):
    p = tmpdir.join('test.pkl')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), allow_pickle=True) == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_file_pickle_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), content_type='application/pickle', allow_pickle=True) == Model(a=12, b=8)


@pytest.mark.xfail(reason='working on V2')
def test_const_differentiates_union():
    class SubModelA(BaseModel):
        key: str = Field('A', const=True)
        foo: int

    class SubModelB(BaseModel):
        key: str = Field('B', const=True)
        foo: int

    class Model(BaseModel):
        a: SubModelA | SubModelB

    m = Model.model_validate({'a': {'key': 'B', 'foo': 3}})
    assert isinstance(m.a, SubModelB)
