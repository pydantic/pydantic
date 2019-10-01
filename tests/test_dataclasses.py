import dataclasses
from datetime import datetime
from pathlib import Path
from typing import ClassVar, FrozenSet, Optional

import pytest

import pydantic
from pydantic import BaseModel, ValidationError, validator


def test_simple():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: float

    d = MyDataclass('1', '2.5')
    assert d.a == 1
    assert d.b == 2.5
    d = MyDataclass(b=10, a=20)
    assert d.a == 20
    assert d.b == 10


def test_value_error():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: int

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(1, 'wrong')

    assert exc_info.value.errors() == [
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_frozen():
    @pydantic.dataclasses.dataclass(frozen=True)
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    with pytest.raises(AttributeError):
        d.a = 7


def test_validate_assignment():
    class Config:
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    d.a = '7'
    assert d.a == 7


def test_validate_assignment_error():
    class Config:
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: int

    d = MyDataclass(1)

    with pytest.raises(ValidationError) as exc_info:
        d.a = 'xxx'
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_not_validate_assignment():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    d.a = '7'
    assert d.a == '7'


def test_validate_assignment_value_change():
    class Config:
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config, frozen=False)
    class MyDataclass:
        a: int

        @validator('a')
        def double_a(cls, v):
            return v * 2

    d = MyDataclass(2)
    assert d.a == 4

    d.a = 3
    assert d.a == 6


def test_validate_assignment_extra():
    class Config:
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config, frozen=False)
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    d.extra_field = 1.23
    assert d.extra_field == 1.23
    d.extra_field = 'bye'
    assert d.extra_field == 'bye'


def test_post_init():
    post_init_called = False

    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int

        def __post_init__(self):
            nonlocal post_init_called
            post_init_called = True

    d = MyDataclass('1')
    assert d.a == 1
    assert post_init_called


def test_post_init_inheritance_chain():
    parent_post_init_called = False
    post_init_called = False

    @pydantic.dataclasses.dataclass
    class ParentDataclass:
        a: int

        def __post_init__(self):
            nonlocal parent_post_init_called
            parent_post_init_called = True

    @pydantic.dataclasses.dataclass
    class MyDataclass(ParentDataclass):
        b: int

        def __post_init__(self):
            super().__post_init__()
            nonlocal post_init_called
            post_init_called = True

    d = MyDataclass(a=1, b=2)
    assert d.a == 1
    assert d.b == 2
    assert parent_post_init_called
    assert post_init_called


def test_post_init_post_parse():
    post_init_post_parse_called = False

    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int

        def __post_init_post_parse__(self):
            nonlocal post_init_post_parse_called
            post_init_post_parse_called = True

    d = MyDataclass('1')
    assert d.a == 1
    assert post_init_post_parse_called


def test_post_init_post_parse_types():
    @pydantic.dataclasses.dataclass
    class CustomType(object):
        b: int

    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: CustomType

        def __post_init__(self):
            assert type(self.a) == dict

        def __post_init_post_parse__(self):
            assert type(self.a) == CustomType

    d = MyDataclass(**{'a': {'b': 1}})
    assert d.a.b == 1


def test_post_init_assignment():
    from dataclasses import field

    # Based on: https://docs.python.org/3/library/dataclasses.html#post-init-processing
    @pydantic.dataclasses.dataclass
    class C:
        a: float
        b: float
        c: float = field(init=False)

        def __post_init__(self):
            self.c = self.a + self.b

    c = C(0.1, 0.2)
    assert c.a == 0.1
    assert c.b == 0.2
    assert c.c == 0.30000000000000004


def test_inheritance():
    @pydantic.dataclasses.dataclass
    class A:
        a: str = None

    @pydantic.dataclasses.dataclass
    class B(A):
        b: int = None

    b = B(a='a', b=12)
    assert b.a == 'a'
    assert b.b == 12

    with pytest.raises(ValidationError):
        B(a='a', b='b')


def test_validate_long_string_error():
    class Config:
        max_anystr_length = 3

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass('xxxx')

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value has at most 3 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 3},
        }
    ]


def test_validate_assigment_long_string_error():
    class Config:
        max_anystr_length = 3
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    d = MyDataclass('xxx')
    with pytest.raises(ValidationError) as exc_info:
        d.a = 'xxxx'

    assert issubclass(MyDataclass.__pydantic_model__.__config__, BaseModel.Config)
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value has at most 3 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 3},
        }
    ]


def test_no_validate_assigment_long_string_error():
    class Config:
        max_anystr_length = 3
        validate_assignment = False

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    d = MyDataclass('xxx')
    d.a = 'xxxx'

    assert d.a == 'xxxx'


def test_nested_dataclass():
    @pydantic.dataclasses.dataclass
    class Nested:
        number: int

    @pydantic.dataclasses.dataclass
    class Outer:
        n: Nested

    navbar = Outer(n=Nested(number='1'))
    assert isinstance(navbar.n, Nested)
    assert navbar.n.number == 1

    navbar = Outer(n=('2',))
    assert isinstance(navbar.n, Nested)
    assert navbar.n.number == 2

    navbar = Outer(n={'number': '3'})
    assert isinstance(navbar.n, Nested)
    assert navbar.n.number == 3

    with pytest.raises(ValidationError) as exc_info:
        Outer(n='not nested')
    assert exc_info.value.errors() == [
        {
            'loc': ('n',),
            'msg': 'instance of Nested, tuple or dict expected',
            'type': 'type_error.dataclass',
            'ctx': {'class_name': 'Nested'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outer(n=('x',))
    assert exc_info.value.errors() == [
        {'loc': ('n', 'number'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_arbitrary_types_allowed():
    @dataclasses.dataclass
    class Button:
        href: str

    class Config:
        arbitrary_types_allowed = True

    @pydantic.dataclasses.dataclass(config=Config)
    class Navbar:
        button: Button

    btn = Button(href='a')
    navbar = Navbar(button=btn)
    assert navbar.button.href == 'a'

    with pytest.raises(ValidationError) as exc_info:
        Navbar(button=('b',))
    assert exc_info.value.errors() == [
        {
            'loc': ('button',),
            'msg': 'instance of Button expected',
            'type': 'type_error.arbitrary_type',
            'ctx': {'expected_arbitrary_type': 'Button'},
        }
    ]


def test_nested_dataclass_model():
    @pydantic.dataclasses.dataclass
    class Nested:
        number: int

    class Outer(BaseModel):
        n: Nested

    navbar = Outer(n=Nested(number='1'))
    assert navbar.n.number == 1


def test_fields():
    @pydantic.dataclasses.dataclass
    class User:
        id: int
        name: str = 'John Doe'
        signup_ts: datetime = None

    user = User(id=123)
    fields = user.__pydantic_model__.__fields__

    assert fields['id'].required is True
    assert fields['id'].default is None

    assert fields['name'].required is False
    assert fields['name'].default == 'John Doe'

    assert fields['signup_ts'].required is False
    assert fields['signup_ts'].default is None


def test_schema():
    @pydantic.dataclasses.dataclass
    class User:
        id: int
        name: str = 'John Doe'
        signup_ts: datetime = None

    user = User(id=123)
    assert user.__pydantic_model__.schema() == {
        'title': 'User',
        'type': 'object',
        'properties': {
            'id': {'title': 'Id', 'type': 'integer'},
            'name': {'title': 'Name', 'default': 'John Doe', 'type': 'string'},
            'signup_ts': {'title': 'Signup Ts', 'type': 'string', 'format': 'date-time'},
        },
        'required': ['id'],
    }


def test_nested_schema():
    @pydantic.dataclasses.dataclass
    class Nested:
        number: int

    @pydantic.dataclasses.dataclass
    class Outer:
        n: Nested

    assert Outer.__pydantic_model__.schema() == {
        'title': 'Outer',
        'type': 'object',
        'properties': {'n': {'$ref': '#/definitions/Nested'}},
        'required': ['n'],
        'definitions': {
            'Nested': {
                'title': 'Nested',
                'type': 'object',
                'properties': {'number': {'title': 'Number', 'type': 'integer'}},
                'required': ['number'],
            }
        },
    }


def test_initvar():
    InitVar = dataclasses.InitVar

    @pydantic.dataclasses.dataclass
    class TestInitVar:
        x: int
        y: InitVar

    tiv = TestInitVar(1, 2)
    assert tiv.x == 1
    with pytest.raises(AttributeError):
        tiv.y


def test_derived_field_from_initvar():
    InitVar = dataclasses.InitVar

    @pydantic.dataclasses.dataclass
    class DerivedWithInitVar:
        plusone: int = dataclasses.field(init=False)
        number: InitVar[int]

        def __post_init__(self, number):
            self.plusone = number + 1

    derived = DerivedWithInitVar(1)
    assert derived.plusone == 2
    with pytest.raises(TypeError):
        DerivedWithInitVar('Not A Number')


def test_initvars_post_init():
    @pydantic.dataclasses.dataclass
    class PathDataPostInit:
        path: Path
        base_path: dataclasses.InitVar[Optional[Path]] = None

        def __post_init__(self, base_path):
            if base_path is not None:
                self.path = base_path / self.path

    path_data = PathDataPostInit('world')
    assert 'path' in path_data.__dict__
    assert 'base_path' not in path_data.__dict__
    assert path_data.path == Path('world')

    with pytest.raises(TypeError) as exc_info:
        PathDataPostInit('world', base_path='/hello')
    assert str(exc_info.value) == "unsupported operand type(s) for /: 'str' and 'str'"


def test_initvars_post_init_post_parse():
    @pydantic.dataclasses.dataclass
    class PathDataPostInitPostParse:
        path: Path
        base_path: dataclasses.InitVar[Optional[Path]] = None

        def __post_init_post_parse__(self, base_path):
            if base_path is not None:
                self.path = base_path / self.path

    path_data = PathDataPostInitPostParse('world')
    assert 'path' in path_data.__dict__
    assert 'base_path' not in path_data.__dict__
    assert path_data.path == Path('world')

    assert PathDataPostInitPostParse('world', base_path='/hello').path == Path('/hello/world')


def test_classvar():
    @pydantic.dataclasses.dataclass
    class TestClassVar:
        klassvar: ClassVar = "I'm a Class variable"
        x: int

    tcv = TestClassVar(2)
    assert tcv.klassvar == "I'm a Class variable"


def test_frozenset_field():
    @pydantic.dataclasses.dataclass
    class TestFrozenSet:
        set: FrozenSet[int]

    test_set = frozenset({1, 2, 3})
    object_under_test = TestFrozenSet(set=test_set)

    assert object_under_test.set == test_set


def test_inheritance_post_init():
    post_init_called = False

    @pydantic.dataclasses.dataclass
    class Base:
        a: int

        def __post_init__(self):
            nonlocal post_init_called
            post_init_called = True

    @pydantic.dataclasses.dataclass
    class Child(Base):
        b: int

    Child(a=1, b=2)
    assert post_init_called
