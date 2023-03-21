from contextlib import nullcontext as does_not_raise
from typing import Any, ContextManager, List, Optional

import pytest

from pydantic import BaseModel, ConfigDict, Extra, ValidationError
from pydantic.fields import Field


@pytest.mark.xfail(reason='working on V2')
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


@pytest.mark.xfail(reason='working on V2')
def test_alias_generator_with_field_schema():
    def to_upper_case(string: str):
        return string.upper()

    class MyModel(BaseModel):
        model_config = ConfigDict(alias_generator=to_upper_case)
        my_shiny_field: Any  # Alias from Config.fields will be used
        foo_bar: str  # Alias from Config.fields will be used
        baz_bar: str  # Alias will be generated
        another_field: str  # Alias will be generated

        class Config:
            fields = {'my_shiny_field': 'MY_FIELD', 'foo_bar': {'alias': 'FOO'}, 'another_field': {'not_alias': 'a'}}

    data = {'MY_FIELD': ['a'], 'FOO': 'bar', 'BAZ_BAR': 'ok', 'ANOTHER_FIELD': '...'}
    m = MyModel(**data)
    assert m.model_dump(by_alias=True) == data


@pytest.mark.xfail(reason='working on V2')
def test_alias_generator_wrong_type_error():
    def return_bytes(string):
        return b'not a string'

    with pytest.raises(TypeError) as e:

        class MyModel(BaseModel):
            model_config = ConfigDict(alias_generator=return_bytes)
            bar: Any

    assert str(e.value) == "Config.alias_generator must return str, not <class 'bytes'>"


@pytest.mark.xfail(reason='working on V2')
def test_cannot_infer_type_with_alias():
    # TODO: I don't think we've finalized the exact error that should be raised when fields are missing annotations,
    #   but this test should be made consistent with that once it is finalized
    with pytest.raises(TypeError):

        class Model(BaseModel):
            a = Field('foobar', alias='_a')


def test_basic_alias():
    class Model(BaseModel):
        a: str = Field('foobar', alias='_a')

    assert Model().a == 'foobar'
    assert Model(_a='different').a == 'different'
    assert repr(Model.model_fields['a']) == (
        "FieldInfo(annotation=str, required=False, default='foobar', alias='_a', alias_priority=2)"
    )


def test_alias_error():
    class Model(BaseModel):
        a: int = Field(123, alias='_a')

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.errors() == [
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
        model_config = ConfigDict(extra=Extra.forbid, populate_by_name=True)
        last_updated_by: Optional[str] = Field(None, alias='lastUpdatedBy')

    assert Model(lastUpdatedBy='foo').model_dump() == {'last_updated_by': 'foo'}
    assert Model(last_updated_by='foo').model_dump() == {'last_updated_by': 'foo'}
    with pytest.raises(ValidationError) as exc_info:
        Model(lastUpdatedBy='foo', last_updated_by='bar')
    assert exc_info.value.errors() == [
        {
            'input': 'bar',
            'loc': ('last_updated_by',),
            'msg': 'Extra inputs are not permitted',
            'type': 'extra_forbidden',
        }
    ]


@pytest.mark.xfail(reason='working on V2')
def test_alias_generator_parent():
    class Parent(BaseModel):
        model_config = ConfigDict(populate_by_name=True, alias_generator=lambda f_name: f_name + '1')
        x: int

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda f_name: f_name + '2')
        y: int

    assert Child.model_fields['y'].alias == 'y2'
    assert Child.model_fields['x'].alias == 'x2'


@pytest.mark.xfail(reason='working on V2')
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


@pytest.mark.xfail(reason='working on V2')
def test_alias_generator_on_child():
    class Parent(BaseModel):
        x: bool = Field(..., alias='abc')
        y: str

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())

        y: str
        z: str

    assert [f.alias for f in Parent.model_fields.values()] == ['abc', 'y']
    assert [f.alias for f in Child.model_fields.values()] == ['abc', 'Y', 'Z']


@pytest.mark.xfail(reason='working on V2')
def test_low_priority_alias():
    # TODO: alias_priority has been removed from `Field`. Should we re-add it?
    #   Is there something new that can be used to replicate this functionality?
    #   See discussion in https://github.com/pydantic/pydantic/pull/5181/files#r1137618854
    #   Either way, if we don't re-add it to `Field`, remember to update the migration guide
    class Parent(BaseModel):
        x: bool = Field(..., alias='abc', alias_priority=1)
        y: str

    class Child(Parent):
        model_config = ConfigDict(alias_generator=lambda x: x.upper())

        y: str
        z: str

    assert [f.alias for f in Parent.model_fields.values()] == ['abc', 'y']
    assert [f.alias for f in Child.model_fields.values()] == ['X', 'Y', 'Z']


@pytest.mark.xfail(reason='working on V2')
def test_low_priority_alias_config():
    class Parent(BaseModel):
        x: bool
        y: str

        class Config:
            fields = {'x': dict(alias='abc', alias_priority=1)}

    class Child(Parent):
        y: str
        z: str

        class Config:
            @staticmethod
            def alias_generator(x):
                return x.upper()

    assert [f.alias for f in Parent.model_fields.values()] == ['abc', 'y']
    assert [f.alias for f in Child.model_fields.values()] == ['X', 'Y', 'Z']


@pytest.mark.xfail(reason='working on V2')
def test_field_vs_config():
    class Model(BaseModel):
        x: str = Field(..., alias='x_on_field')
        y: str
        z: str

        class Config:
            fields = {'x': dict(alias='x_on_config'), 'y': dict(alias='y_on_config')}

    assert [f.alias for f in Model.model_fields.values()] == ['x_on_field', 'y_on_config', 'z']


@pytest.mark.xfail(reason='working on V2')
def test_alias_priority():
    class Parent(BaseModel):
        a: str = Field(..., alias='a_field_parent')
        b: str = Field(..., alias='b_field_parent')
        c: str = Field(..., alias='c_field_parent')
        d: str
        e: str

        class Config:
            fields = {
                'a': dict(alias='a_config_parent'),
                'c': dict(alias='c_config_parent'),
                'd': dict(alias='d_config_parent'),
            }

            @staticmethod
            def alias_generator(x):
                return f'{x}_generator_parent'

    class Child(Parent):
        a: str = Field(..., alias='a_field_child')

        class Config:
            fields = {'a': dict(alias='a_config_child'), 'b': dict(alias='b_config_child')}

            @staticmethod
            def alias_generator(x):
                return f'{x}_generator_child'

    # debug([f.alias for f in Parent.model_fields.values()], [f.alias for f in Child.model_fields.values()])
    assert [f.alias for f in Parent.model_fields.values()] == [
        'a_field_parent',
        'b_field_parent',
        'c_field_parent',
        'd_config_parent',
        'e_generator_parent',
    ]
    assert [f.alias for f in Child.model_fields.values()] == [
        'a_field_child',
        'b_config_child',
        'c_field_parent',
        'd_config_parent',
        'e_generator_child',
    ]


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
