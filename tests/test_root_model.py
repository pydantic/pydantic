import pickle
from datetime import date, datetime
from typing import Any, Dict, Generic, List, Optional, Union

import pytest
from pydantic_core import CoreSchema
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from typing_extensions import Annotated, Literal, TypeVar

from pydantic import (
    Base64Str,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    PydanticDeprecatedSince20,
    PydanticUserError,
    RootModel,
    ValidationError,
    field_serializer,
    model_validator,
)


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


def check_schema(schema: CoreSchema) -> None:
    # we assume the shape of the core schema here, which is not a guarantee
    # pydantic makes to its users but is useful to check here to make sure
    # we are doing the right thing internally
    assert schema['type'] == 'model'
    assert schema['root_model'] is True
    assert schema['custom_init'] is False


@parametrize_root_model()
def test_root_model_specialized(root_type, root_value, dump_value):
    Model = RootModel[root_type]

    check_schema(Model.__pydantic_core_schema__)

    m = Model(root_value)

    assert m.model_dump() == dump_value
    assert dict(m) == {'root': m.root}
    assert m.__pydantic_fields_set__ == {'root'}


@parametrize_root_model()
def test_root_model_inherited(root_type, root_value, dump_value):
    class Model(RootModel[root_type]):
        pass

    check_schema(Model.__pydantic_core_schema__)

    m = Model(root_value)

    assert m.model_dump() == dump_value
    assert dict(m) == {'root': m.root}
    assert m.__pydantic_fields_set__ == {'root'}


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
    with pytest.warns(PydanticDeprecatedSince20):
        assert m.dict() == {'my_root': {'__root__': {'x': 1}}}


def test_construct():
    class Base64Root(RootModel[Base64Str]):
        pass

    v = Base64Root.model_construct('test')
    assert v.model_dump() == 'dGVzdA==\n'


def test_construct_nested():
    class Base64RootProperty(BaseModel):
        data: RootModel[Base64Str]

    v = Base64RootProperty.model_construct(data=RootModel[Base64Str].model_construct('test'))
    assert v.model_dump() == {'data': 'dGVzdA==\n'}

    # Note: model_construct requires the inputs to be valid; the root model value does not get "validated" into
    # an actual root model instance:
    v = Base64RootProperty.model_construct(data='test')
    assert isinstance(v.data, str)  # should be RootModel[Base64Str], but model_construct skipped validation
    with pytest.raises(AttributeError, match="'str' object has no attribute 'root'"):
        v.model_dump()


def test_assignment():
    Model = RootModel[int]

    m = Model(1)
    assert m.model_fields_set == {'root'}
    assert m.root == 1
    m.root = 2
    assert m.root == 2


def test_model_validator_before():
    class Model(RootModel[int]):
        @model_validator(mode='before')
        @classmethod
        def words(cls, v):
            if v == 'one':
                return 1
            elif v == 'two':
                return 2
            else:
                return v

    assert Model('one').root == 1
    assert Model('two').root == 2
    assert Model('3').root == 3
    with pytest.raises(ValidationError) as exc_info:
        Model('three')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'three',
        }
    ]


def test_model_validator_after():
    class Model(RootModel[int]):
        @model_validator(mode='after')
        def double(self) -> 'Model':
            self.root *= 2
            return self

    assert Model('1').root == 2
    assert Model('21').root == 42


def test_private_attr():
    class Model(RootModel[int]):
        _private_attr: str
        _private_attr_default: str = PrivateAttr(default='abc')

    m = Model(42)

    assert m.root == 42
    assert m._private_attr_default == 'abc'
    with pytest.raises(AttributeError, match='_private_attr'):
        m._private_attr

    m._private_attr = 7
    m._private_attr_default = 8
    m._other_private_attr = 9
    # TODO: Should this be an `AttributeError`?
    with pytest.raises(ValueError, match='other_attr'):
        m.other_attr = 10

    assert m._private_attr == 7
    assert m._private_attr_default == 8
    assert m._other_private_attr == 9
    assert m.model_dump() == 42


def test_validate_assignment_false():
    Model = RootModel[int]

    m = Model(42)
    m.root = 'abc'
    assert m.root == 'abc'


def test_validate_assignment_true():
    class Model(RootModel[int]):
        model_config = ConfigDict(validate_assignment=True)

    m = Model(42)

    with pytest.raises(ValidationError) as e:
        m.root = 'abc'

    assert e.value.errors(include_url=False) == [
        {
            'input': 'abc',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_root_model_literal():
    assert RootModel[int](42).root == 42


def test_root_model_equality():
    assert RootModel[int](42) == RootModel[int](42)
    assert RootModel[int](42) != RootModel[int](7)
    assert RootModel[int](42) != RootModel[float](42)
    assert RootModel[int](42) == RootModel[int].model_construct(42)


def test_root_model_with_private_attrs_equality():
    class Model(RootModel[int]):
        _private_attr: str = PrivateAttr(default='abc')

    m = Model(42)
    assert m == Model(42)

    m._private_attr = 'xyz'
    assert m != Model(42)


def test_root_model_nested_equality():
    class Model(BaseModel):
        value: RootModel[int]

    assert Model(value=42).value == RootModel[int](42)


def test_root_model_base_model_equality():
    class R(RootModel[int]):
        pass

    class B(BaseModel):
        root: int

    assert R(42) != B(root=42)
    assert B(root=42) != R(42)


@pytest.mark.parametrize('extra_value', ['ignore', 'allow', 'forbid'])
def test_extra_error(extra_value):
    with pytest.raises(PydanticUserError, match='extra'):

        class Model(RootModel[int]):
            model_config = ConfigDict(extra=extra_value)


def test_root_model_default_value():
    class Model(RootModel):
        root: int = 42

    m = Model()
    assert m.root == 42
    assert m.model_dump() == 42
    assert m.__pydantic_fields_set__ == set()


def test_root_model_default_factory():
    class Model(RootModel):
        root: int = Field(default_factory=lambda: 42)

    m = Model()
    assert m.root == 42
    assert m.model_dump() == 42
    assert m.__pydantic_fields_set__ == set()


def test_root_model_wrong_default_value_without_validate_default():
    class Model(RootModel):
        root: int = '42'

    assert Model().root == '42'


def test_root_model_default_value_with_validate_default():
    class Model(RootModel):
        model_config = ConfigDict(validate_default=True)

        root: int = '42'

    m = Model()
    assert m.root == 42
    assert m.model_dump() == 42
    assert m.__pydantic_fields_set__ == set()


def test_root_model_default_value_with_validate_default_on_field():
    class Model(RootModel):
        root: Annotated[int, Field(validate_default=True, default='42')]

    m = Model()
    assert m.root == 42
    assert m.model_dump() == 42
    assert m.__pydantic_fields_set__ == set()


def test_root_model_as_attr_with_validate_default():
    class Model(BaseModel):
        model_config = ConfigDict(validate_default=True)

        rooted_value: RootModel[int] = 42

    m = Model()
    assert m.rooted_value == RootModel[int](42)
    assert m.model_dump() == {'rooted_value': 42}
    assert m.rooted_value.__pydantic_fields_set__ == {'root'}


def test_root_model_in_root_model_default():
    class Nested(RootModel):
        root: int = 42

    class Model(RootModel):
        root: Nested = Nested()

    m = Model()
    assert m.root.root == 42
    assert m.__pydantic_fields_set__ == set()
    assert m.root.__pydantic_fields_set__ == set()


def test_nested_root_model_naive_default():
    class Nested(RootModel):
        root: int = 42

    class Model(BaseModel):
        value: Nested

    m = Model(value=Nested())
    assert m.value.root == 42
    assert m.value.__pydantic_fields_set__ == set()


def test_nested_root_model_proper_default():
    class Nested(RootModel):
        root: int = 42

    class Model(BaseModel):
        value: Nested = Field(default_factory=Nested)

    m = Model()
    assert m.value.root == 42
    assert m.value.__pydantic_fields_set__ == set()


def test_root_model_json_schema_meta():
    ParametrizedModel = RootModel[int]

    class SubclassedModel(RootModel):
        """Subclassed Model docstring"""

        root: int

    parametrized_json_schema = ParametrizedModel.model_json_schema()
    subclassed_json_schema = SubclassedModel.model_json_schema()

    assert parametrized_json_schema.get('title') == 'RootModel[int]'
    assert parametrized_json_schema.get('description') is None
    assert subclassed_json_schema.get('title') == 'SubclassedModel'
    assert subclassed_json_schema.get('description') == 'Subclassed Model docstring'


@pytest.mark.parametrize('order', ['BR', 'RB'])
def test_root_model_dump_with_base_model(order):
    class BModel(BaseModel):
        value: str

    class RModel(RootModel):
        root: int

    if order == 'BR':

        class Model(RootModel):
            root: List[Union[BModel, RModel]]

    elif order == 'RB':

        class Model(RootModel):
            root: List[Union[RModel, BModel]]

    m = Model([1, 2, {'value': 'abc'}])

    assert m.root == [RModel(1), RModel(2), BModel.model_construct(value='abc')]
    assert m.model_dump() == [1, 2, {'value': 'abc'}]
    assert m.model_dump_json() == '[1,2,{"value":"abc"}]'


@pytest.mark.parametrize(
    'data',
    [
        pytest.param({'kind': 'IModel', 'int_value': 42}, id='IModel'),
        pytest.param({'kind': 'SModel', 'str_value': 'abc'}, id='SModel'),
    ],
)
def test_mixed_discriminated_union(data):
    class IModel(BaseModel):
        kind: Literal['IModel']
        int_value: int

    class RModel(RootModel):
        root: IModel

    class SModel(BaseModel):
        kind: Literal['SModel']
        str_value: str

    class Model(RootModel):
        root: Union[SModel, RModel] = Field(discriminator='kind')

    assert Model(data).model_dump() == data
    assert Model(**data).model_dump() == data


def test_list_rootmodel():
    class A(BaseModel):
        type: Literal['a']
        a: str

    class B(BaseModel):
        type: Literal['b']
        b: str

    class D(RootModel[Annotated[Union[A, B], Field(discriminator='type')]]):
        pass

    LD = RootModel[List[D]]

    obj = LD.model_validate([{'type': 'a', 'a': 'a'}, {'type': 'b', 'b': 'b'}])
    assert obj.model_dump() == [{'type': 'a', 'a': 'a'}, {'type': 'b', 'b': 'b'}]


def test_root_and_data_error():
    class BModel(BaseModel):
        value: int
        other_value: str

    Model = RootModel[BModel]

    with pytest.raises(
        ValueError,
        match='"RootModel.__init__" accepts either a single positional argument or arbitrary keyword arguments',
    ):
        Model({'value': 42}, other_value='abc')


def test_pickle_root_model(create_module):
    @create_module
    def module():
        from pydantic import RootModel

        class MyRootModel(RootModel[str]):
            pass

    MyRootModel = module.MyRootModel
    assert MyRootModel(root='abc') == pickle.loads(pickle.dumps(MyRootModel(root='abc')))


def test_json_schema_extra_on_model():
    class Model(RootModel):
        model_config = ConfigDict(json_schema_extra={'schema key': 'schema value'})
        root: str

    assert Model.model_json_schema() == {
        'schema key': 'schema value',
        'title': 'Model',
        'type': 'string',
    }


def test_json_schema_extra_on_field():
    class Model(RootModel):
        root: str = Field(json_schema_extra={'schema key': 'schema value'})

    assert Model.model_json_schema() == {
        'schema key': 'schema value',
        'title': 'Model',
        'type': 'string',
    }


def test_json_schema_extra_on_model_and_on_field():
    class Model(RootModel):
        model_config = ConfigDict(json_schema_extra={'schema key on model': 'schema value on model'})
        root: str = Field(json_schema_extra={'schema key on field': 'schema value on field'})

    with pytest.raises(ValueError, match=r'json_schema_extra.*?must not be set simultaneously'):
        Model.model_json_schema()


def test_help(create_module):
    module = create_module(
        # language=Python
        """
import pydoc

from pydantic import RootModel


help_result_string = pydoc.render_doc(RootModel)
"""
    )
    assert 'class RootModel' in module.help_result_string


def test_copy_preserves_equality():
    model = RootModel()

    copied = model.__copy__()
    assert model == copied

    deepcopied = model.__deepcopy__()
    assert model == deepcopied


@pytest.mark.parametrize(
    'root_type,input_value,expected,raises_match,strict',
    [
        (bool, 'true', True, None, False),
        (bool, 'true', True, None, True),
        (bool, 'false', False, None, False),
        (bool, 'e', ValidationError, 'type=bool_parsing', False),
        (int, '1', 1, None, False),
        (int, '1', 1, None, True),
        (int, 'xxx', ValidationError, 'type=int_parsing', True),
        (float, '1.1', 1.1, None, False),
        (float, '1.10', 1.1, None, False),
        (float, '1.1', 1.1, None, True),
        (float, '1.10', 1.1, None, True),
        (date, '2017-01-01', date(2017, 1, 1), None, False),
        (date, '2017-01-01', date(2017, 1, 1), None, True),
        (date, '2017-01-01T12:13:14.567', ValidationError, 'type=date_from_datetime_inexact', False),
        (date, '2017-01-01T12:13:14.567', ValidationError, 'type=date_parsing', True),
        (date, '2017-01-01T00:00:00', date(2017, 1, 1), None, False),
        (date, '2017-01-01T00:00:00', ValidationError, 'type=date_parsing', True),
        (datetime, '2017-01-01T12:13:14.567', datetime(2017, 1, 1, 12, 13, 14, 567_000), None, False),
        (datetime, '2017-01-01T12:13:14.567', datetime(2017, 1, 1, 12, 13, 14, 567_000), None, True),
    ],
    ids=repr,
)
def test_model_validate_strings(root_type, input_value, expected, raises_match, strict):
    Model = RootModel[root_type]

    if raises_match is not None:
        with pytest.raises(expected, match=raises_match):
            Model.model_validate_strings(input_value, strict=strict)
    else:
        assert Model.model_validate_strings(input_value, strict=strict).root == expected


def test_model_construction_with_invalid_generic_specification() -> None:
    T_ = TypeVar('T_', bound=BaseModel)

    with pytest.raises(TypeError, match='You should parametrize RootModel directly'):

        class GenericRootModel(RootModel, Generic[T_]):
            root: Union[T_, int]


def test_model_with_field_description() -> None:
    class AModel(RootModel):
        root: int = Field(description='abc')

    assert AModel.model_json_schema() == {'title': 'AModel', 'type': 'integer', 'description': 'abc'}


def test_model_with_both_docstring_and_field_description() -> None:
    """Check if the docstring is used as the description when both are present."""

    class AModel(RootModel):
        """More detailed description"""

        root: int = Field(description='abc')

    assert AModel.model_json_schema() == {
        'title': 'AModel',
        'type': 'integer',
        'description': 'More detailed description',
    }
