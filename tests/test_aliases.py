import re
from typing import Optional

import pytest

from pydantic import BaseConfig, BaseModel, Extra, ValidationError
from pydantic.fields import Field


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


def test_population_by_alias():
    with pytest.warns(DeprecationWarning, match='"allow_population_by_alias" is deprecated and replaced by'):

        class Model(BaseModel):
            a: str

            class Config:
                allow_population_by_alias = True
                fields = {'a': {'alias': '_a'}}

    assert Model.__config__.allow_population_by_field_name is True
    assert Model(a='different').a == 'different'
    assert Model(a='different').dict() == {'a': 'different'}
    assert Model(a='different').dict(by_alias=True) == {'_a': 'different'}


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
