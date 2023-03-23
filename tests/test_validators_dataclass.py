import re
from dataclasses import asdict, is_dataclass
from typing import Any, List

import pytest
from dirty_equals import HasRepr, IsStr

from pydantic import ValidationError, root_validator
from pydantic.dataclasses import dataclass
from pydantic.decorators import field_validator


def test_simple():
    @dataclass
    class MyDataclass:
        a: str

        @field_validator('a')
        @classmethod
        def change_a(cls, v):
            return v + ' changed'

    assert MyDataclass(a='this is foobar good').a == 'this is foobar good changed'


def test_validate_before():
    @dataclass
    class MyDataclass:
        a: List[int]

        @field_validator('a', mode='before')
        @classmethod
        def check_a1(cls, v: List[Any]) -> List[Any]:
            v.append('123')
            return v

        @field_validator('a')
        @classmethod
        def check_a2(cls, v: List[int]) -> List[int]:
            v.append(456)
            return v

    assert MyDataclass(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_multiple():
    @dataclass
    class MyDataclass:
        a: str
        b: str

        @field_validator('a', 'b')
        @classmethod
        def check_a_and_b(cls, v, info):
            if len(v) < 4:
                raise ValueError(f'{info.field_name} is too short')
            return v + 'x'

    assert asdict(MyDataclass(a='1234', b='5678')) == {'a': '1234x', 'b': '5678x'}

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a='x', b='x')
    assert exc_info.value.errors() == [
        {
            'ctx': {'error': 'a is too short'},
            'input': 'x',
            'loc': ('a',),
            'msg': 'Value error, a is too short',
            'type': 'value_error',
        },
        {
            'ctx': {'error': 'b is too short'},
            'input': 'x',
            'loc': ('b',),
            'msg': 'Value error, b is too short',
            'type': 'value_error',
        },
    ]


def test_type_error():
    @dataclass
    class MyDataclass:
        a: str
        b: str

        @field_validator('a', 'b')
        @classmethod
        def check_a_and_b(cls, v, info):
            if len(v) < 4:
                raise TypeError(f'{info.field_name} is too short')
            return v + 'x'

    assert asdict(MyDataclass(a='1234', b='5678')) == {'a': '1234x', 'b': '5678x'}

    with pytest.raises(TypeError, match='a is too short'):
        MyDataclass(a='x', b='x')


def test_classmethod():
    @dataclass
    class MyDataclass:
        a: str

        @field_validator('a')
        @classmethod
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

        @field_validator('a')
        @classmethod
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

        @field_validator('a')
        @classmethod
        def add_to_a(cls, v):
            return v + 1

    @dataclass
    class Child(Parent):
        @field_validator('a')
        @classmethod
        def add_to_a(cls, v):
            return v + 5

    assert Child(a=0).a == 5


def test_root_validator():
    root_val_values = []

    @dataclass
    class MyDataclass:
        a: int
        b: str

        @field_validator('b')
        @classmethod
        def repeat_b(cls, v):
            return v * 2

        @root_validator(skip_on_failure=True)
        def root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

    assert asdict(MyDataclass(a='123', b='bar')) == {'a': 123, 'b': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(1, b='snap dragon')
    assert root_val_values == [{'a': 123, 'b': 'barbar'}, {'a': 1, 'b': 'snap dragonsnap dragon'}]

    assert exc_info.value.errors() == [
        {
            'ctx': {'error': 'foobar'},
            'input': HasRepr(IsStr(regex=re.escape("ArgsKwargs(args=(1,), kwargs={'b': 'snap dragon'})"))),
            'loc': (),
            'msg': 'Value error, foobar',
            'type': 'value_error',
        }
    ]
