from dataclasses import asdict, is_dataclass
from typing import List

import pytest

from pydantic import ValidationError, root_validator, validator
from pydantic.dataclasses import dataclass


def test_simple():
    @dataclass
    class MyDataclass:
        a: str

        @validator('a')
        def change_a(cls, v):
            return v + ' changed'

    assert MyDataclass(a='this is foobar good').a == 'this is foobar good changed'


def test_validate_pre():
    @dataclass
    class MyDataclass:
        a: List[int]

        @validator('a', pre=True)
        def check_a1(cls, v):
            v.append('123')
            return v

        @validator('a')
        def check_a2(cls, v):
            v.append(456)
            return v

    assert MyDataclass(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_multiple():
    # also test TypeError
    @dataclass
    class MyDataclass:
        a: str
        b: str

        @validator('a', 'b')
        def check_a_and_b(cls, v, field, **kwargs):
            if len(v) < 4:
                raise TypeError(f'{field.alias} is too short')
            return v + 'x'

    assert asdict(MyDataclass(a='1234', b='5678')) == {'a': '1234x', 'b': '5678x'}

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a='x', b='x')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'a is too short', 'type': 'type_error'},
        {'loc': ('b',), 'msg': 'b is too short', 'type': 'type_error'},
    ]


def test_classmethod():
    @dataclass
    class MyDataclass:
        a: str

        @validator('a')
        def check_a(cls, v):
            assert cls is MyDataclass and is_dataclass(MyDataclass)
            return v

    m = MyDataclass(a='this is foobar good')
    assert m.a == 'this is foobar good'
    m.check_a('x')


def test_validate_parent():
    @dataclass
    class Parent:
        a: str

        @validator('a')
        def change_a(cls, v):
            return v + ' changed'

    @dataclass
    class Child(Parent):
        pass

    assert Parent(a='this is foobar good').a == 'this is foobar good changed'
    assert Child(a='this is foobar good').a == 'this is foobar good changed'


def test_inheritance_replace():
    @dataclass
    class Parent:
        a: int

        @validator('a')
        def add_to_a(cls, v):
            return v + 1

    @dataclass
    class Child(Parent):
        @validator('a')
        def add_to_a(cls, v):
            return v + 5

    assert Child(a=0).a == 5


def test_root_validator():
    root_val_values = []

    @dataclass
    class MyDataclass:
        a: int
        b: str

        @validator('b')
        def repeat_b(cls, v):
            return v * 2

        @root_validator
        def root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

    assert asdict(MyDataclass(a='123', b='bar')) == {'a': 123, 'b': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a=1, b='snap dragon')
    assert root_val_values == [{'a': 123, 'b': 'barbar'}, {'a': 1, 'b': 'snap dragonsnap dragon'}]

    assert exc_info.value.errors() == [{'loc': ('__root__',), 'msg': 'foobar', 'type': 'value_error'}]
