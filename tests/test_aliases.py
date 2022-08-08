import re
from contextlib import nullcontext as does_not_raise
from typing import Any, ContextManager, List, Optional

import pytest

from pydantic import BaseConfig, BaseModel, Extra, ValidationError
from pydantic.fields import Field


def test_alias_generator():
    def to_camel(string: str):
        return ''.join(x.capitalize() for x in string.split('_'))

    class MyModel(BaseModel):
        a: List[str] = None
        foo_bar: str

        class Config:
            alias_generator = to_camel

    data = {'A': ['foo', 'bar'], 'FooBar': 'foobar'}
    v = MyModel(**data)
    assert v.a == ['foo', 'bar']
    assert v.foo_bar == 'foobar'
    assert v.dict(by_alias=True) == data


def test_alias_generator_with_field_schema():
    def to_upper_case(string: str):
        return string.upper()

    class MyModel(BaseModel):
        my_shiny_field: Any  # Alias from Config.fields will be used
        foo_bar: str  # Alias from Config.fields will be used
        baz_bar: str  # Alias will be generated
        another_field: str  # Alias will be generated

        class Config:
            alias_generator = to_upper_case
            fields = {'my_shiny_field': 'MY_FIELD', 'foo_bar': {'alias': 'FOO'}, 'another_field': {'not_alias': 'a'}}

    data = {'MY_FIELD': ['a'], 'FOO': 'bar', 'BAZ_BAR': 'ok', 'ANOTHER_FIELD': '...'}
    m = MyModel(**data)
    assert m.dict(by_alias=True) == data


def test_alias_generator_wrong_type_error():
    def return_bytes(string):
        return b'not a string'

    with pytest.raises(TypeError) as e:

        class MyModel(BaseModel):
            bar: Any

            class Config:
                alias_generator = return_bytes

    assert str(e.value) == "Config.alias_generator must return str, not <class 'bytes'>"


def test_infer_alias():
    class Model(BaseModel):
        a = 'foobar'

        class Config:
            fields = {'a': '_a'}

    assert Model(_a='different').a == 'different'
    assert repr(Model.__fields__['a']) == (
        "ModelField(name='a', type=str, required=False, default='foobar', alias='_a')"
    )


def test_alias_error():
    class Model(BaseModel):
        a = 123

        class Config:
            fields = {'a': '_a'}

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.errors() == [
        {'loc': ('_a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_annotation_config():
    class Model(BaseModel):
        b: float
        a: int = 10
        _c: str

        class Config:
            fields = {'b': 'foobar'}

    assert list(Model.__fields__.keys()) == ['b', 'a']
    assert [f.alias for f in Model.__fields__.values()] == ['foobar', 'a']
    assert Model(foobar='123').b == 123.0


def test_alias_camel_case():
    class Model(BaseModel):
        one_thing: int
        another_thing: int

        class Config(BaseConfig):
            @classmethod
            def get_field_info(cls, name):
                field_config = super().get_field_info(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'(?:^|_)([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    v = Model(**{'OneThing': 123, 'AnotherThing': '321'})
    assert v.one_thing == 123
    assert v.another_thing == 321
    assert v == {'one_thing': 123, 'another_thing': 321}


def test_get_field_info_inherit():
    class ModelOne(BaseModel):
        class Config(BaseConfig):
            @classmethod
            def get_field_info(cls, name):
                field_config = super().get_field_info(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    class ModelTwo(ModelOne):
        one_thing: int
        another_thing: int
        third_thing: int

        class Config:
            fields = {'third_thing': 'Banana'}

    v = ModelTwo(**{'oneThing': 123, 'anotherThing': '321', 'Banana': 1})
    assert v == {'one_thing': 123, 'another_thing': 321, 'third_thing': 1}


def test_pop_by_field_name():
    class Model(BaseModel):
        last_updated_by: Optional[str] = None

        class Config:
            extra = Extra.forbid
            allow_population_by_field_name = True
            fields = {'last_updated_by': 'lastUpdatedBy'}

    assert Model(lastUpdatedBy='foo').dict() == {'last_updated_by': 'foo'}
    assert Model(last_updated_by='foo').dict() == {'last_updated_by': 'foo'}
    with pytest.raises(ValidationError) as exc_info:
        Model(lastUpdatedBy='foo', last_updated_by='bar')
    assert exc_info.value.errors() == [
        {'loc': ('last_updated_by',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'}
    ]


def test_alias_child_precedence():
    class Parent(BaseModel):
        x: int

        class Config:
            fields = {'x': 'x1'}

    class Child(Parent):
        y: int

        class Config:
            fields = {'y': 'y2', 'x': 'x2'}

    assert Child.__fields__['y'].alias == 'y2'
    assert Child.__fields__['x'].alias == 'x2'


def test_alias_generator_parent():
    class Parent(BaseModel):
        x: int

        class Config:
            allow_population_by_field_name = True

            @classmethod
            def alias_generator(cls, f_name):
                return f_name + '1'

    class Child(Parent):
        y: int

        class Config:
            @classmethod
            def alias_generator(cls, f_name):
                return f_name + '2'

    assert Child.__fields__['y'].alias == 'y2'
    assert Child.__fields__['x'].alias == 'x2'


def test_alias_generator_on_parent():
    class Parent(BaseModel):
        x: bool = Field(..., alias='a_b_c')
        y: str

        class Config:
            @staticmethod
            def alias_generator(x):
                return x.upper()

    class Child(Parent):
        y: str
        z: str

    assert Parent.__fields__['x'].alias == 'a_b_c'
    assert Parent.__fields__['y'].alias == 'Y'
    assert Child.__fields__['x'].alias == 'a_b_c'
    assert Child.__fields__['y'].alias == 'Y'
    assert Child.__fields__['z'].alias == 'Z'


def test_alias_generator_on_child():
    class Parent(BaseModel):
        x: bool = Field(..., alias='abc')
        y: str

    class Child(Parent):
        y: str
        z: str

        class Config:
            @staticmethod
            def alias_generator(x):
                return x.upper()

    assert [f.alias for f in Parent.__fields__.values()] == ['abc', 'y']
    assert [f.alias for f in Child.__fields__.values()] == ['abc', 'Y', 'Z']


def test_low_priority_alias():
    class Parent(BaseModel):
        x: bool = Field(..., alias='abc', alias_priority=1)
        y: str

    class Child(Parent):
        y: str
        z: str

        class Config:
            @staticmethod
            def alias_generator(x):
                return x.upper()

    assert [f.alias for f in Parent.__fields__.values()] == ['abc', 'y']
    assert [f.alias for f in Child.__fields__.values()] == ['X', 'Y', 'Z']


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

    assert [f.alias for f in Parent.__fields__.values()] == ['abc', 'y']
    assert [f.alias for f in Child.__fields__.values()] == ['X', 'Y', 'Z']


def test_field_vs_config():
    class Model(BaseModel):
        x: str = Field(..., alias='x_on_field')
        y: str
        z: str

        class Config:
            fields = {'x': dict(alias='x_on_config'), 'y': dict(alias='y_on_config')}

    assert [f.alias for f in Model.__fields__.values()] == ['x_on_field', 'y_on_config', 'z']


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

    # debug([f.alias for f in Parent.__fields__.values()], [f.alias for f in Child.__fields__.values()])
    assert [f.alias for f in Parent.__fields__.values()] == [
        'a_field_parent',
        'b_field_parent',
        'c_field_parent',
        'd_config_parent',
        'e_generator_parent',
    ]
    assert [f.alias for f in Child.__fields__.values()] == [
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
    assert m.dict(by_alias=True) == data


@pytest.mark.parametrize(
    'use_construct, allow_population_by_field_name_config, arg_name, expectation',
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
def test_allow_population_by_field_name_config(
    use_construct: bool,
    allow_population_by_field_name_config: bool,
    arg_name: str,
    expectation: ContextManager,
):
    expected_value: int = 7

    class Foo(BaseModel):
        bar_: int = Field(..., alias='bar')

        class Config(BaseConfig):
            allow_population_by_field_name = allow_population_by_field_name_config

    with expectation:
        if use_construct:
            f = Foo.construct(**{arg_name: expected_value})
        else:
            f = Foo(**{arg_name: expected_value})

        assert f.bar_ == expected_value
