from typing import List, Tuple

import pytest

from pydantic import BaseModel, ValidationError, model_validator, parse_obj_as
from pydantic.functional_serializers import model_serializer


class Model(BaseModel):
    a: float
    b: int = 10


def test_obj():
    m = Model.model_validate(dict(a=10.2))
    assert str(m) == 'a=10.2 b=10'


def test_model_validate_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate([1, 2, 3])
    assert exc_info.value.errors(include_url=False) == [
        {'input': [1, 2, 3], 'loc': (), 'msg': 'Input should be a valid dictionary', 'type': 'dict_type'}
    ]


def test_model_validate_submodel():
    m = Model.model_validate(Model(a=10.2))
    assert m.model_dump() == {'a': 10.2, 'b': 10}


def test_model_validate_wrong_model():
    class Foo(BaseModel):
        c: int = 123

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate(Foo())
    assert exc_info.value.errors(include_url=False) == [
        {'input': Foo(), 'loc': (), 'msg': 'Input should be a valid dictionary', 'type': 'dict_type'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate(Foo().model_dump())
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'c': 123}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_root_model_error():
    with pytest.raises(
        TypeError,
        match='__root__ models are no longer supported in v2',
    ):

        class MyModel(BaseModel):
            __root__: str


def test_model_validate_root():
    class MyModel(BaseModel):
        root: str

        # Note that the following three definitions require no changes across all __root__ models
        # I couldn't see a nice way to create a decorator that reduces the boilerplate,
        # but if we want to discourage this pattern, perhaps that's okay?
        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def __get_pydantic_json_schema__(cls, core_schema, handler):
            json_schema = handler(core_schema)
            return json_schema['properties']['root']

    # Validation
    m = MyModel.model_validate('a')
    assert m.root == 'a'

    # Serialization
    # TODO: Possible concern — `model_dump` is annotated as returning dict[str, Any] — is that okay, given
    #   model_serializer could change that? Should we try to reflect it in the mypy plugin?
    assert m.model_dump() == {'root': 'a'}
    assert m.model_dump_json() == '"a"'

    # JSON schema
    assert m.model_json_schema() == {'title': 'Root', 'type': 'string'}


def test_parse_root_list():
    class MyModel(BaseModel):
        root: List[str]

        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    m = MyModel.model_validate(['a'])
    assert m.model_dump() == {'root': ['a']}
    assert m.model_dump_json() == '["a"]'
    assert m.root == ['a']


def test_parse_nested_root_list():
    class NestedData(BaseModel):
        id: str

    class NestedModel(BaseModel):
        root: List[NestedData]

        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    class MyModel(BaseModel):
        nested: NestedModel

    m = MyModel.model_validate({'nested': [{'id': 'foo'}]})
    assert isinstance(m.nested, NestedModel)
    assert isinstance(m.nested.root[0], NestedData)


@pytest.mark.filterwarnings('ignore:parse_obj_as is deprecated.*:DeprecationWarning')
def test_parse_nested_root_tuple():
    class NestedData(BaseModel):
        id: str

    class NestedModel(BaseModel):
        root: Tuple[int, NestedData]

        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    class MyModel(BaseModel):
        nested: List[NestedModel]

    data = [0, {'id': 'foo'}]
    m = MyModel.model_validate({'nested': [data]})
    assert isinstance(m.nested[0], NestedModel)
    assert isinstance(m.nested[0].root[1], NestedData)

    nested = parse_obj_as(NestedModel, data)
    assert isinstance(nested, NestedModel)


def test_parse_nested_custom_root():
    class NestedModel(BaseModel):
        root: List[str]

        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    class MyModel(BaseModel):
        root: NestedModel

        @model_validator(mode='before')
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    nested = ['foo', 'bar']
    m = MyModel.model_validate(nested)
    assert isinstance(m, MyModel)
    assert isinstance(m.root, NestedModel)
    assert isinstance(m.root.root, List)
    assert isinstance(m.root.root[0], str)


def test_json():
    assert Model.model_validate_json('{"a": 12, "b": 8}') == Model(a=12, b=8)
