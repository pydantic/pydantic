from typing import Any, Dict, List, Optional

import pytest
from pydantic_core.core_schema import SerializerFunctionWrapHandler

from pydantic import BaseModel, RootModel, ValidationError, field_serializer


def parametrize_root_model():
    class InnerModel(BaseModel):
        int_field: int
        str_field: str

    return pytest.mark.parametrize(
        ('root_type', 'root_value', 'dump_value'),
        [
            pytest.param(int, 42, 42, id='int'),
            pytest.param(str, 'forty two', 'forty two', id='str'),
            pytest.param(Dict[int, bool], {1: True, 2: False}, {1: True, 2: False}, id='dict[int, bool]'),
            pytest.param(List[int], [4, 2, -1], [4, 2, -1], id='list[int]'),
            pytest.param(
                InnerModel,
                InnerModel(int_field=42, str_field='forty two'),
                {'int_field': 42, 'str_field': 'forty two'},
                id='InnerModel',
            ),
        ],
    )


@parametrize_root_model()
def test_root_model_specialized(root_type, root_value, dump_value):
    Model = RootModel[root_type]

    assert Model.__pydantic_core_schema__['type'] == 'model'
    assert Model.__pydantic_core_schema__['root_model'] is True
    assert Model.__pydantic_core_schema__['custom_init'] is False

    m = Model(root_value)

    assert m.model_dump() == dump_value
    assert dict(m) == {'root': m.root}


@parametrize_root_model()
def test_root_model_inherited(root_type, root_value, dump_value):
    class Model(RootModel[root_type]):
        pass

    assert Model.__pydantic_core_schema__['type'] == 'model'
    assert Model.__pydantic_core_schema__['root_model'] is True
    assert Model.__pydantic_core_schema__['custom_init'] is False

    m = Model(root_value)

    assert m.model_dump() == dump_value
    assert dict(m) == {'root': m.root}


def test_root_model_validation_error():
    Model = RootModel[int]

    with pytest.raises(ValidationError) as e:
        Model('forty two')

    assert e.value.errors(include_url=False) == [
        {
            'input': 'forty two',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


def test_root_model_repr():
    SpecializedRootModel = RootModel[int]

    class SubRootModel(RootModel):
        pass

    class SpecializedSubRootModel(RootModel[int]):
        pass

    assert repr(SpecializedRootModel(1)) == 'RootModel[int](root=1)'
    assert repr(SubRootModel(1)) == 'SubRootModel(root=1)'
    assert repr(SpecializedSubRootModel(1)) == 'SpecializedSubRootModel(root=1)'


def test_root_model_recursive():
    class A(RootModel[List['B']]):
        def my_a_method(self):
            pass

    class B(RootModel[Dict[str, Optional[A]]]):
        def my_b_method(self):
            pass

    assert repr(A.model_validate([{}])) == 'A(root=[B(root={})])'


def test_root_model_nested():
    calls = []

    class B(RootModel[int]):
        def my_b_method(self):
            calls.append(('my_b_method', self.root))

    class A(RootModel[B]):
        def my_a_method(self):
            calls.append(('my_a_method', self.root.root))

    m1 = A.model_validate(1)
    m1.my_a_method()
    m1.root.my_b_method()
    assert calls == [('my_a_method', 1), ('my_b_method', 1)]

    calls.clear()
    m2 = A.model_validate_json('2')
    m2.my_a_method()
    m2.root.my_b_method()
    assert calls == [('my_a_method', 2), ('my_b_method', 2)]


def test_root_model_as_field():
    class MyRootModel(RootModel[int]):
        pass

    class MyModel(BaseModel):
        root_model: MyRootModel

    m = MyModel.model_validate({'root_model': 1})

    assert isinstance(m.root_model, MyRootModel)


def test_v1_compatibility_serializer():
    class MyInnerModel(BaseModel):
        x: int

    class MyRootModel(RootModel[MyInnerModel]):
        # The following field_serializer can be added to achieve the same behavior as v1 had for .dict()
        @field_serializer('root', mode='wrap')
        def embed_in_dict(self, v: Any, handler: SerializerFunctionWrapHandler):
            return {'__root__': handler(v)}

    class MyOuterModel(BaseModel):
        my_root: MyRootModel

    m = MyOuterModel.model_validate({'my_root': {'x': 1}})

    assert m.model_dump() == {'my_root': {'__root__': {'x': 1}}}
    with pytest.warns(DeprecationWarning):
        assert m.dict() == {'my_root': {'__root__': {'x': 1}}}
