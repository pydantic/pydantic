from dataclasses import asdict, is_dataclass
from typing import List

import pytest

from pydantic import ValidationError, validator
from pydantic.dataclasses import dataclass


def test_simple():
    @dataclass
    class MyDataclass:
        a: str

        @validator('a')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert MyDataclass(a='this is foobar good').a == 'this is foobar good'

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a='snap')
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': '"foobar" not found in a', 'type': 'value_error'}]


def test_validate_whole():
    @dataclass
    class MyDataclass:
        a: List[int]

        @validator('a', whole=True, pre=True)
        def check_a1(cls, v):
            v.append('123')
            return v

        @validator('a', whole=True)
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
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    @dataclass
    class Child(Parent):
        pass

    assert Parent(a='this is foobar good').a == 'this is foobar good'
    assert Child(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        Parent(a='snap')
    with pytest.raises(ValidationError):
        Child(a='snap')
