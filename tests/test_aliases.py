from contextlib import nullcontext as does_not_raise
from inspect import signature
from typing import Any, ContextManager, List, Optional

import pytest
from dirty_equals import IsStr

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.fields import AliasChoices, AliasPath, Field


def test_alias_generator():
    def to_camel(string: str):
        return ''.join(x.capitalize() for x in string.split('_'))

    class MyModel(BaseModel):
        model_config = ConfigDict(alias_generator=to_camel)
        a: List[str] = None
        foo_bar: str

    data = {'A': ['foo', 'bar'], 'FooBar': 'foobar'}
    v = MyModel(**data)
    assert v.a == ['foo', 'bar']
    assert v.foo_bar == 'foobar'
    assert v.model_dump(by_alias=True) == data


def test_alias_generator_wrong_type_error():
    def return_bytes(string):
        return b'not a string'

    with pytest.raises(TypeError) as e:

        class MyModel(BaseModel):
            model_config = ConfigDict(alias_generator=return_bytes)
            bar: Any

    assert str(e.value) == IsStr(regex="alias_generator <function .*> must return str, not <class 'bytes'>")


def test_basic_alias():
    class Model(BaseModel):
        a: str = Field('foobar', alias='_a')

    assert Model().a == 'foobar'
    assert Model(_a='different').a == 'different'
    assert repr(Model.model_fields['a']) == (
        "FieldInfo(annotation=str, required=False, default='foobar', alias='_a', alias_priority=2)"
    )


def test_field_info_repr_with_aliases():
    class Model(BaseModel):
        a: str = Field('foobar', alias='_a', validation_alias='a_val', serialization_alias='a_ser')

    assert repr(Model.model_fields['a']) == (
        "FieldInfo(annotation=str, required=False, default='foobar', alias='_a', "
        "alias_priority=2, validation_alias='a_val', serialization_alias='a_ser')"
    )


def test_alias_error():
    class Model(BaseModel):
        a: int = Field(123, alias='_a')

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'foo',
            'loc': ('_a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_alias_error_loc_by_alias():
    class Model(BaseModel):
        model_config = dict(loc_by_alias=False)
        a: int = Field(123, alias='_a')

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'foo',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_annotation_config():
    class Model(BaseModel):
        b: float = Field(alias='foobar')
        a: int = 10
        _c: str

    assert list(Model.model_fields.keys()) == ['b', 'a']
    assert [f.alias for f in Model.model_fields.values()] == ['foobar', None]
    assert Model(foobar='123').b == 123.0


def test_pop_by_field_name():
    class Model(BaseModel):
        model_config = ConfigDict(extra='forbid', populate_by_name=True)
        last_updated_by: Optional[str] = Field(None, alias='lastUpdatedBy')

    assert Model(lastUpdatedBy='foo').model_dump() == {'last_updated_by': 'foo'}
    assert Model(last_updated_by='foo').model_dump() == {'last_updated_by': 'foo'}
    with pytest.raises(ValidationError) as exc_info:
        Model(lastUpdatedBy='foo', last_updated_by='bar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'bar',
            'loc': ('last_updated_by',),
            'msg': 'Extra inputs are not permitted',
            'type': 'extra_forbidden',
        }
    ]


def test_alias_override_behavior():
    class Parent(BaseModel):
        # Use `gt` to demonstrate that using `Field` to override an alias does not preserve other attributes
        x: int = Field(alias='x1', gt=0)

    class Child(Parent):
        x: int = Field(..., alias='x2')
        y: int = Field(..., alias='y2')

    assert Parent.model_fields['x'].alias == 'x1'
    assert Child.model_fields['x'].alias == 'x2'
    assert Child.model_fields['y'].alias == 'y2'

    Parent(x1=1)
    with pytest.raises(ValidationError) as exc_info:
        Parent(x1=-1)
    assert exc_info.value.errors(include_url=False) == [
        {'ctx': {'gt': 0}, 'input': -1, 'loc': ('x1',), 'msg': 'Input should be greater than 0', 'type': 'greater_than'}
    ]

    Child(x2=1, y2=2)

    # Check the gt=0 is not preserved from Parent
    Child(x2=-1, y2=2)

    # Check the alias from Parent cannot be used
    with pytest.raises(ValidationError) as exc_info:
        Child(x1=1, y2=2)
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'x1': 1, 'y2': 2}, 'loc': ('x2',), 'msg': 'Field required', 'type': 'missing'}
    ]

    # Check the type hint from Parent _is_ preserved
    with pytest.raises(ValidationError) as exc_info:
        Child(x2='a', y2=2)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('x2',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_alias_generator_parent():
    class Parent(BaseModel):
        model_config = ConfigDict(populate_by_name=True, alias_generator=lambda f_name: f_name + '1')
        x: int

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda f_name: f_name + '2')
        y: int

    assert Child.model_fields['y'].alias == 'y2'
    assert Child.model_fields['x'].alias == 'x2'


def test_alias_generator_on_parent():
    class Parent(BaseModel):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())
        x: bool = Field(..., alias='a_b_c')
        y: str

    class Child(Parent):
        y: str
        z: str

    assert Parent.model_fields['x'].alias == 'a_b_c'
    assert Parent.model_fields['y'].alias == 'Y'
    assert Child.model_fields['x'].alias == 'a_b_c'
    assert Child.model_fields['y'].alias == 'Y'
    assert Child.model_fields['z'].alias == 'Z'


def test_alias_generator_on_child():
    class Parent(BaseModel):
        x: bool = Field(..., alias='abc')
        y: str

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())

        y: str
        z: str

    assert [f.alias for f in Parent.model_fields.values()] == ['abc', None]
    assert [f.alias for f in Child.model_fields.values()] == ['abc', 'Y', 'Z']


def test_low_priority_alias():
    class Parent(BaseModel):
        w: bool = Field(..., alias='w_', validation_alias='w_val_alias', serialization_alias='w_ser_alias')
        x: bool = Field(
            ..., alias='abc', alias_priority=1, validation_alias='x_val_alias', serialization_alias='x_ser_alias'
        )
        y: str

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())

        y: str
        z: str

    assert [f.alias for f in Parent.model_fields.values()] == ['w_', 'abc', None]
    assert [f.validation_alias for f in Parent.model_fields.values()] == ['w_val_alias', 'x_val_alias', None]
    assert [f.serialization_alias for f in Parent.model_fields.values()] == ['w_ser_alias', 'x_ser_alias', None]
    assert [f.alias for f in Child.model_fields.values()] == ['w_', 'X', 'Y', 'Z']
    assert [f.validation_alias for f in Child.model_fields.values()] == ['w_val_alias', 'X', 'Y', 'Z']
    assert [f.serialization_alias for f in Child.model_fields.values()] == ['w_ser_alias', 'X', 'Y', 'Z']


@pytest.mark.parametrize(
    'cls_params, field_params, validation_key, serialization_key',
    [
        pytest.param(
            {},
            {'alias': 'x1', 'validation_alias': 'x2'},
            'x2',
            'x1',
            id='alias-validation_alias',
        ),
        pytest.param(
            {'alias_generator': str.upper},
            {'alias': 'x'},
            'x',
            'x',
            id='alias_generator-alias',
        ),
        pytest.param(
            {'alias_generator': str.upper},
            {'alias': 'x1', 'validation_alias': 'x2'},
            'x2',
            'x1',
            id='alias_generator-alias-validation_alias',
        ),
        pytest.param(
            {'alias_generator': str.upper},
            {'alias': 'x1', 'serialization_alias': 'x2'},
            'x1',
            'x2',
            id='alias_generator-alias-serialization_alias',
        ),
        pytest.param(
            {'alias_generator': str.upper},
            {'alias': 'x1', 'validation_alias': 'x2', 'serialization_alias': 'x3'},
            'x2',
            'x3',
            id='alias_generator-alias-validation_alias-serialization_alias',
        ),
    ],
)
def test_aliases_priority(cls_params, field_params, validation_key, serialization_key):
    class Model(BaseModel, **cls_params):
        x: int = Field(**field_params)

    model = Model(**{validation_key: 1})
    assert model.x == 1
    assert model.model_dump(by_alias=True).get(serialization_key, None) is not None


def test_empty_string_alias():
    class Model(BaseModel):
        empty_string_key: int = Field(alias='')

    data = {'': 123}
    m = Model(**data)
    assert m.empty_string_key == 123
    assert m.model_dump(by_alias=True) == data


@pytest.mark.parametrize(
    'use_construct, populate_by_name_config, arg_name, expectation',
    [
        [False, True, 'bar', does_not_raise()],
        [False, True, 'bar_', does_not_raise()],
        [False, False, 'bar', does_not_raise()],
        [False, False, 'bar_', pytest.raises(ValueError)],
        [True, True, 'bar', does_not_raise()],
        [True, True, 'bar_', does_not_raise()],
        [True, False, 'bar', does_not_raise()],
        [True, False, 'bar_', does_not_raise()],
    ],
)
def test_populate_by_name_config(
    use_construct: bool,
    populate_by_name_config: bool,
    arg_name: str,
    expectation: ContextManager,
):
    expected_value: int = 7

    class Foo(BaseModel):
        model_config = ConfigDict(populate_by_name=populate_by_name_config)
        bar_: int = Field(..., alias='bar')

    with expectation:
        if use_construct:
            f = Foo.model_construct(**{arg_name: expected_value})
        else:
            f = Foo(**{arg_name: expected_value})

        assert f.bar_ == expected_value


def test_validation_alias():
    class Model(BaseModel):
        x: str = Field(validation_alias='foo')

    data = {'foo': 'bar'}
    m = Model(**data)
    assert m.x == 'bar'

    with pytest.raises(ValidationError) as exc_info:
        Model(x='bar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('foo',),
            'msg': 'Field required',
            'input': {'x': 'bar'},
        }
    ]


def test_validation_alias_with_alias():
    class Model(BaseModel):
        x: str = Field(alias='x_alias', validation_alias='foo')

    data = {'foo': 'bar'}
    m = Model(**data)
    assert m.x == 'bar'
    sig = signature(Model)
    assert 'x_alias' in sig.parameters

    with pytest.raises(ValidationError) as exc_info:
        Model(x='bar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('foo',),
            'msg': 'Field required',
            'input': {'x': 'bar'},
        }
    ]


def test_validation_alias_from_str_alias():
    class Model(BaseModel):
        x: str = Field(alias='foo')

    data = {'foo': 'bar'}
    m = Model(**data)
    assert m.x == 'bar'
    sig = signature(Model)
    assert 'foo' in sig.parameters

    with pytest.raises(ValidationError) as exc_info:
        Model(x='bar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('foo',),
            'msg': 'Field required',
            'input': {'x': 'bar'},
        }
    ]


def test_validation_alias_from_list_alias():
    class Model(BaseModel):
        x: str = Field(alias=['foo', 'bar'])

    data = {'foo': {'bar': 'test'}}
    m = Model(**data)
    assert m.x == 'test'
    sig = signature(Model)
    assert 'x' in sig.parameters

    class Model(BaseModel):
        x: str = Field(alias=['foo', 1])

    data = {'foo': ['bar0', 'bar1']}
    m = Model(**data)
    assert m.x == 'bar1'
    sig = signature(Model)
    assert 'x' in sig.parameters


def test_serialization_alias():
    class Model(BaseModel):
        x: str = Field(serialization_alias='foo')

    m = Model(x='bar')
    assert m.x == 'bar'
    assert m.model_dump() == {'x': 'bar'}
    assert m.model_dump(by_alias=True) == {'foo': 'bar'}


def test_serialization_alias_with_alias():
    class Model(BaseModel):
        x: str = Field(alias='x_alias', serialization_alias='foo')

    data = {'x_alias': 'bar'}
    m = Model(**data)
    assert m.x == 'bar'
    assert m.model_dump() == {'x': 'bar'}
    assert m.model_dump(by_alias=True) == {'foo': 'bar'}
    sig = signature(Model)
    assert 'x_alias' in sig.parameters


def test_serialization_alias_from_alias():
    class Model(BaseModel):
        x: str = Field(alias='foo')

    data = {'foo': 'bar'}
    m = Model(**data)
    assert m.x == 'bar'
    assert m.model_dump() == {'x': 'bar'}
    assert m.model_dump(by_alias=True) == {'foo': 'bar'}
    sig = signature(Model)
    assert 'foo' in sig.parameters


@pytest.mark.parametrize(
    'field,expected',
    [
        pytest.param(
            Field(alias='x_alias', validation_alias='x_val_alias', serialization_alias='x_ser_alias'),
            {
                'properties': {'x_val_alias': {'title': 'X Val Alias', 'type': 'string'}},
                'required': ['x_val_alias'],
            },
            id='single_alias',
        ),
        pytest.param(
            Field(validation_alias=AliasChoices('y_alias', 'another_alias')),
            {
                'properties': {'y_alias': {'title': 'Y Alias', 'type': 'string'}},
                'required': ['y_alias'],
            },
            id='multiple_aliases',
        ),
        pytest.param(
            Field(validation_alias=AliasChoices(AliasPath('z_alias', 'even_another_alias'), 'and_another')),
            {
                'properties': {'and_another': {'title': 'And Another', 'type': 'string'}},
                'required': ['and_another'],
            },
            id='multiple_aliases_with_path',
        ),
    ],
)
def test_aliases_json_schema(field, expected):
    class Model(BaseModel):
        x: str = field

    assert Model.model_json_schema() == {'title': 'Model', 'type': 'object', **expected}


@pytest.mark.parametrize(
    'value',
    [
        'a',
        AliasPath('a', 'b', 1),
        AliasChoices('a', 'b'),
        AliasChoices('a', AliasPath('b', 1)),
    ],
)
def test_validation_alias_path(value):
    class Model(BaseModel):
        x: str = Field(validation_alias=value)

    assert Model.model_fields['x'].validation_alias == value


def test_validation_alias_invalid_value_type():
    m = 'Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`'
    with pytest.raises(TypeError, match=m):

        class Model(BaseModel):
            x: str = Field(validation_alias=123)


def test_validation_alias_parse_data():
    class Model(BaseModel):
        x: str = Field(validation_alias=AliasChoices('a', AliasPath('b', 1), 'c'))

    assert Model.model_fields['x'].validation_alias == AliasChoices('a', AliasPath('b', 1), 'c')
    assert Model.model_validate({'a': 'hello'}).x == 'hello'
    assert Model.model_validate({'b': ['hello', 'world']}).x == 'world'
    assert Model.model_validate({'c': 'test'}).x == 'test'
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'b': ['hello']})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('a',),
            'msg': 'Field required',
            'input': {'b': ['hello']},
        }
    ]
