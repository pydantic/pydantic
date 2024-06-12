import dataclasses
import inspect
import pickle
import re
import sys
import traceback
from collections.abc import Hashable
from dataclasses import InitVar
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, FrozenSet, Generic, List, Optional, Set, TypeVar, Union

import pytest
from dirty_equals import HasRepr
from pydantic_core import ArgsKwargs, CoreSchema, SchemaValidator, core_schema
from typing_extensions import Annotated, Literal

import pydantic
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    GenerateSchema,
    PydanticDeprecatedSince20,
    PydanticUndefinedAnnotation,
    PydanticUserError,
    RootModel,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
    with_config,
)
from pydantic._internal._mock_val_ser import MockValSer
from pydantic.dataclasses import is_pydantic_dataclass, rebuild_dataclass
from pydantic.fields import Field, FieldInfo
from pydantic.json_schema import model_json_schema


def test_cannot_create_dataclass_from_basemodel_subclass():
    msg = 'Cannot create a Pydantic dataclass from SubModel as it is already a Pydantic model'

    with pytest.raises(PydanticUserError, match=msg):

        @pydantic.dataclasses.dataclass
        class SubModel(BaseModel):
            pass


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


def test_model_name():
    @pydantic.dataclasses.dataclass
    class MyDataClass:
        model_name: str

    d = MyDataClass('foo')
    assert d.model_name == 'foo'
    d = MyDataClass(model_name='foo')
    assert d.model_name == 'foo'


def test_value_error():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: int

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(1, 'wrong')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
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
    @pydantic.dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    d.a = '7'
    assert d.a == 7


def test_validate_assignment_error():
    @pydantic.dataclasses.dataclass(config=ConfigDict(validate_assignment=True))
    class MyDataclass:
        a: int

    d = MyDataclass(1)

    with pytest.raises(ValidationError) as exc_info:
        d.a = 'xxx'
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xxx',
        }
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
    @pydantic.dataclasses.dataclass(config=ConfigDict(validate_assignment=True), frozen=False)
    class MyDataclass:
        a: int

        @field_validator('a')
        @classmethod
        def double_a(cls, v: int) -> int:
            return v * 2

    d = MyDataclass(2)
    assert d.a == 4

    d.a = 3
    assert d.a == 6


@pytest.mark.parametrize(
    'config',
    [
        ConfigDict(validate_assignment=False),
        ConfigDict(extra=None),
        ConfigDict(extra='forbid'),
        ConfigDict(extra='ignore'),
        ConfigDict(validate_assignment=False, extra=None),
        ConfigDict(validate_assignment=False, extra='forbid'),
        ConfigDict(validate_assignment=False, extra='ignore'),
        ConfigDict(validate_assignment=False, extra='allow'),
        ConfigDict(validate_assignment=True, extra='allow'),
    ],
)
def test_validate_assignment_extra_unknown_field_assigned_allowed(config: ConfigDict):
    @pydantic.dataclasses.dataclass(config=config)
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    d.extra_field = 123
    assert d.extra_field == 123


@pytest.mark.parametrize(
    'config',
    [
        ConfigDict(validate_assignment=True),
        ConfigDict(validate_assignment=True, extra=None),
        ConfigDict(validate_assignment=True, extra='forbid'),
        ConfigDict(validate_assignment=True, extra='ignore'),
    ],
)
def test_validate_assignment_extra_unknown_field_assigned_errors(config: ConfigDict):
    @pydantic.dataclasses.dataclass(config=config)
    class MyDataclass:
        a: int

    d = MyDataclass(1)
    assert d.a == 1

    with pytest.raises(ValidationError) as exc_info:
        d.extra_field = 1.23

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('extra_field',),
            'msg': "Object has no attribute 'extra_field'",
            'input': 1.23,
            'ctx': {'attribute': 'extra_field'},
        }
    ]


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


def test_post_init_validation():
    @dataclasses.dataclass
    class DC:
        a: int

        def __post_init__(self):
            self.a *= 2

    assert DC(a='2').a == '22'
    PydanticDC = pydantic.dataclasses.dataclass(DC)
    assert DC(a='2').a == '22'
    assert PydanticDC(a='2').a == 4


def test_convert_vanilla_dc():
    @dataclasses.dataclass
    class DC:
        a: int
        b: str = dataclasses.field(init=False)

        def __post_init__(self):
            self.a *= 2
            self.b = 'hello'

    dc1 = DC(a='2')
    assert dc1.a == '22'
    assert dc1.b == 'hello'
    PydanticDC = pydantic.dataclasses.dataclass(DC)
    dc2 = DC(a='2')
    assert dc2.a == '22'
    assert dc2.b == 'hello'

    py_dc = PydanticDC(a='2')
    assert py_dc.a == 4
    assert py_dc.b == 'hello'


def test_std_dataclass_with_parent():
    @dataclasses.dataclass
    class DCParent:
        a: int

    @dataclasses.dataclass
    class DC(DCParent):
        b: int

        def __post_init__(self):
            self.a *= 2

    assert dataclasses.asdict(DC(a='2', b='1')) == {'a': '22', 'b': '1'}
    PydanticDC = pydantic.dataclasses.dataclass(DC)
    assert dataclasses.asdict(DC(a='2', b='1')) == {'a': '22', 'b': '1'}
    assert dataclasses.asdict(PydanticDC(a='2', b='1')) == {'a': 4, 'b': 1}


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
    with pytest.warns(PydanticDeprecatedSince20, match='Support for `__post_init_post_parse__` has been dropped'):

        @pydantic.dataclasses.dataclass
        class MyDataclass:
            a: int

            def __post_init_post_parse__(self):
                pass


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

    a_ = A(a=b'a')
    assert a_.a == 'a'

    @pydantic.dataclasses.dataclass
    class B(A):
        b: int = None

    b = B(a='a', b=12)
    assert b.a == 'a'
    assert b.b == 12

    with pytest.raises(ValidationError):
        B(a='a', b='b')

    a_ = A(a=b'a')
    assert a_.a == 'a'


def test_validate_long_string_error():
    @pydantic.dataclasses.dataclass(config=dict(str_max_length=3))
    class MyDataclass:
        a: str

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass('xxxx')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': (0,),
            'msg': 'String should have at most 3 characters',
            'input': 'xxxx',
            'ctx': {'max_length': 3},
        }
    ]


def test_validate_assignment_long_string_error():
    @pydantic.dataclasses.dataclass(config=ConfigDict(str_max_length=3, validate_assignment=True))
    class MyDataclass:
        a: str

    d = MyDataclass('xxx')
    with pytest.raises(ValidationError) as exc_info:
        d.a = 'xxxx'

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('a',),
            'msg': 'String should have at most 3 characters',
            'input': 'xxxx',
            'ctx': {'max_length': 3},
        }
    ]


def test_no_validate_assignment_long_string_error():
    @pydantic.dataclasses.dataclass(config=ConfigDict(str_max_length=3, validate_assignment=False))
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

    navbar = Outer(n={'number': '3'})
    assert isinstance(navbar.n, Nested)
    assert navbar.n.number == 3

    with pytest.raises(ValidationError) as exc_info:
        Outer(n='not nested')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dataclass_type',
            'loc': ('n',),
            'msg': 'Input should be a dictionary or an instance of Nested',
            'input': 'not nested',
            'ctx': {'class_name': 'Nested'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Outer(n={'number': 'x'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('n', 'number'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        }
    ]


def test_arbitrary_types_allowed():
    class Button:
        def __init__(self, href: str):
            self.href = href

    @pydantic.dataclasses.dataclass(config=dict(arbitrary_types_allowed=True))
    class Navbar:
        button: Button

    btn = Button(href='a')
    navbar = Navbar(button=btn)
    assert navbar.button.href == 'a'

    with pytest.raises(ValidationError) as exc_info:
        Navbar(button=('b',))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('button',),
            'msg': 'Input should be an instance of test_arbitrary_types_allowed.<locals>.Button',
            'input': ('b',),
            'ctx': {'class': 'test_arbitrary_types_allowed.<locals>.Button'},
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
    fields = user.__pydantic_fields__

    assert fields['id'].is_required() is True

    assert fields['name'].is_required() is False
    assert fields['name'].default == 'John Doe'

    assert fields['signup_ts'].is_required() is False
    assert fields['signup_ts'].default is None


@pytest.mark.parametrize('field_constructor', [dataclasses.field, pydantic.dataclasses.Field])
def test_default_factory_field(field_constructor: Callable):
    @pydantic.dataclasses.dataclass
    class User:
        id: int
        other: Dict[str, str] = field_constructor(default_factory=lambda: {'John': 'Joey'})

    user = User(id=123)

    assert user.id == 123
    assert user.other == {'John': 'Joey'}
    fields = user.__pydantic_fields__

    assert fields['id'].is_required() is True
    assert repr(fields['id'].default) == 'PydanticUndefined'

    assert fields['other'].is_required() is False
    assert fields['other'].default_factory() == {'John': 'Joey'}


def test_default_factory_singleton_field():
    class MySingleton:
        pass

    MY_SINGLETON = MySingleton()

    @pydantic.dataclasses.dataclass(config=dict(arbitrary_types_allowed=True))
    class Foo:
        singleton: MySingleton = dataclasses.field(default_factory=lambda: MY_SINGLETON)

    # Returning a singleton from a default_factory is supported
    assert Foo().singleton is Foo().singleton


def test_schema():
    @pydantic.dataclasses.dataclass
    class User:
        id: int
        name: str = 'John Doe'
        aliases: Dict[str, str] = dataclasses.field(default_factory=lambda: {'John': 'Joey'})
        signup_ts: datetime = None
        age: Optional[int] = dataclasses.field(
            default=None, metadata=dict(title='The age of the user', description='do not lie!')
        )
        height: Optional[int] = pydantic.Field(None, title='The height in cm', ge=50, le=300)

    User(id=123)
    assert model_json_schema(User) == {
        'properties': {
            'age': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'title': 'The age of the user',
                'description': 'do not lie!',
            },
            'aliases': {
                'additionalProperties': {'type': 'string'},
                'title': 'Aliases',
                'type': 'object',
            },
            'height': {
                'anyOf': [{'maximum': 300, 'minimum': 50, 'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'title': 'The height in cm',
            },
            'id': {'title': 'Id', 'type': 'integer'},
            'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
            'signup_ts': {'default': None, 'format': 'date-time', 'title': 'Signup Ts', 'type': 'string'},
        },
        'required': ['id'],
        'title': 'User',
        'type': 'object',
    }


def test_nested_schema():
    @pydantic.dataclasses.dataclass
    class Nested:
        number: int

    @pydantic.dataclasses.dataclass
    class Outer:
        n: Nested

    assert model_json_schema(Outer) == {
        '$defs': {
            'Nested': {
                'properties': {'number': {'title': 'Number', 'type': 'integer'}},
                'required': ['number'],
                'title': 'Nested',
                'type': 'object',
            }
        },
        'properties': {'n': {'$ref': '#/$defs/Nested'}},
        'required': ['n'],
        'title': 'Outer',
        'type': 'object',
    }


def test_initvar():
    @pydantic.dataclasses.dataclass
    class TestInitVar:
        x: int
        y: dataclasses.InitVar

    tiv = TestInitVar(1, 2)
    assert tiv.x == 1
    with pytest.raises(AttributeError):
        tiv.y


def test_derived_field_from_initvar():
    @pydantic.dataclasses.dataclass
    class DerivedWithInitVar:
        plusone: int = dataclasses.field(init=False)
        number: dataclasses.InitVar[int]

        def __post_init__(self, number):
            self.plusone = number + 1

    derived = DerivedWithInitVar('1')
    assert derived.plusone == 2
    with pytest.raises(ValidationError, match='Input should be a valid integer, unable to parse string as an integer'):
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

    p = PathDataPostInit('world', base_path='/hello')
    assert p.path == Path('/hello/world')


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


def test_hashable_required():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        v: Hashable

    MyDataclass(v=None)
    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(v=[])
    assert exc_info.value.errors(include_url=False) == [
        {'input': [], 'loc': ('v',), 'msg': 'Input should be hashable', 'type': 'is_hashable'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        # Should this raise a TypeError instead? https://github.com/pydantic/pydantic/issues/5487
        MyDataclass()
    assert exc_info.value.errors(include_url=False) == [
        {'input': HasRepr('ArgsKwargs(())'), 'loc': ('v',), 'msg': 'Field required', 'type': 'missing'}
    ]


@pytest.mark.parametrize('default', [1, None])
def test_default_value(default):
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        v: int = default

    assert dataclasses.asdict(MyDataclass()) == {'v': default}
    assert dataclasses.asdict(MyDataclass(v=42)) == {'v': 42}


def test_default_value_ellipsis():
    """
    https://github.com/pydantic/pydantic/issues/5488
    """

    @pydantic.dataclasses.dataclass
    class MyDataclass:
        v: int = ...

    assert dataclasses.asdict(MyDataclass(v=42)) == {'v': 42}
    with pytest.raises(ValidationError, match='type=missing'):
        MyDataclass()


def test_override_builtin_dataclass():
    @dataclasses.dataclass
    class File:
        hash: str
        name: Optional[str]
        size: int
        content: Optional[bytes] = None

    ValidFile = pydantic.dataclasses.dataclass(File)

    file = File(hash='xxx', name=b'whatever.txt', size='456')
    valid_file = ValidFile(hash='xxx', name=b'whatever.txt', size='456')

    assert file.name == b'whatever.txt'
    assert file.size == '456'

    assert valid_file.name == 'whatever.txt'
    assert valid_file.size == 456

    assert isinstance(valid_file, File)
    assert isinstance(valid_file, ValidFile)

    with pytest.raises(ValidationError) as e:
        ValidFile(hash=[1], name='name', size=3)

    assert e.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('hash',),
            'msg': 'Input should be a valid string',
            'input': [1],
        },
    ]


def test_override_builtin_dataclass_2():
    @dataclasses.dataclass
    class Meta:
        modified_date: Optional[datetime]
        seen_count: int

    Meta(modified_date='not-validated', seen_count=0)

    @pydantic.dataclasses.dataclass
    @dataclasses.dataclass
    class File(Meta):
        filename: str

    Meta(modified_date='still-not-validated', seen_count=0)

    f = File(filename=b'thefilename', modified_date='2020-01-01T00:00', seen_count='7')
    assert f.filename == 'thefilename'
    assert f.modified_date == datetime(2020, 1, 1, 0, 0)
    assert f.seen_count == 7


def test_override_builtin_dataclass_nested():
    @dataclasses.dataclass
    class Meta:
        modified_date: Optional[datetime]
        seen_count: int

    @dataclasses.dataclass
    class File:
        filename: str
        meta: Meta

    FileChecked = pydantic.dataclasses.dataclass(File, config=ConfigDict(revalidate_instances='always'))
    f = FileChecked(filename=b'thefilename', meta=Meta(modified_date='2020-01-01T00:00', seen_count='7'))
    assert f.filename == 'thefilename'
    assert f.meta.modified_date == datetime(2020, 1, 1, 0, 0)
    assert f.meta.seen_count == 7

    with pytest.raises(ValidationError) as e:
        FileChecked(filename=b'thefilename', meta=Meta(modified_date='2020-01-01T00:00', seen_count=['7']))
    # insert_assert(e.value.errors(include_url=False))
    assert e.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('meta', 'seen_count'), 'msg': 'Input should be a valid integer', 'input': ['7']}
    ]

    class Foo(
        BaseModel,
    ):
        file: File

    foo = Foo.model_validate(
        {
            'file': {
                'filename': b'thefilename',
                'meta': {'modified_date': '2020-01-01T00:00', 'seen_count': '7'},
            },
        }
    )
    assert foo.file.filename == 'thefilename'
    assert foo.file.meta.modified_date == datetime(2020, 1, 1, 0, 0)
    assert foo.file.meta.seen_count == 7


def test_override_builtin_dataclass_nested_schema():
    @dataclasses.dataclass
    class Meta:
        modified_date: Optional[datetime]
        seen_count: int

    @dataclasses.dataclass
    class File:
        filename: str
        meta: Meta

    FileChecked = pydantic.dataclasses.dataclass(File)
    assert model_json_schema(FileChecked) == {
        '$defs': {
            'Meta': {
                'properties': {
                    'modified_date': {
                        'anyOf': [{'format': 'date-time', 'type': 'string'}, {'type': 'null'}],
                        'title': 'Modified Date',
                    },
                    'seen_count': {'title': 'Seen Count', 'type': 'integer'},
                },
                'required': ['modified_date', 'seen_count'],
                'title': 'Meta',
                'type': 'object',
            }
        },
        'properties': {'filename': {'title': 'Filename', 'type': 'string'}, 'meta': {'$ref': '#/$defs/Meta'}},
        'required': ['filename', 'meta'],
        'title': 'File',
        'type': 'object',
    }


def test_inherit_builtin_dataclass():
    @dataclasses.dataclass
    class Z:
        z: int

    @dataclasses.dataclass
    class Y(Z):
        y: int

    @pydantic.dataclasses.dataclass
    class X(Y):
        x: int

    pika = X(x='2', y='4', z='3')
    assert pika.x == 2
    assert pika.y == 4
    assert pika.z == 3


def test_forward_stdlib_dataclass_params():
    @dataclasses.dataclass(frozen=True)
    class Item:
        name: str

    class Example(BaseModel):
        item: Item
        other: str

        model_config = ConfigDict(arbitrary_types_allowed=True)

    e = Example(item=Item(name='pika'), other='bulbi')
    e.other = 'bulbi2'
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.item.name = 'pika2'


def test_pydantic_callable_field():
    """pydantic callable fields behaviour should be the same as stdlib dataclass"""

    def foo(arg1, arg2):
        return arg1, arg2

    def bar(x: int, y: float, z: str) -> bool:
        return str(x + y) == z

    class PydanticModel(BaseModel):
        required_callable: Callable
        required_callable_2: Callable[[int, float, str], bool]

        default_callable: Callable = foo
        default_callable_2: Callable[[int, float, str], bool] = bar

    @pydantic.dataclasses.dataclass
    class PydanticDataclass:
        required_callable: Callable
        required_callable_2: Callable[[int, float, str], bool]

        default_callable: Callable = foo
        default_callable_2: Callable[[int, float, str], bool] = bar

    @dataclasses.dataclass
    class StdlibDataclass:
        required_callable: Callable
        required_callable_2: Callable[[int, float, str], bool]

        default_callable: Callable = foo
        default_callable_2: Callable[[int, float, str], bool] = bar

    pyd_m = PydanticModel(required_callable=foo, required_callable_2=bar)
    pyd_dc = PydanticDataclass(required_callable=foo, required_callable_2=bar)
    std_dc = StdlibDataclass(required_callable=foo, required_callable_2=bar)

    assert (
        pyd_m.required_callable
        is pyd_m.default_callable
        is pyd_dc.required_callable
        is pyd_dc.default_callable
        is std_dc.required_callable
        is std_dc.default_callable
    )
    assert (
        pyd_m.required_callable_2
        is pyd_m.default_callable_2
        is pyd_dc.required_callable_2
        is pyd_dc.default_callable_2
        is std_dc.required_callable_2
        is std_dc.default_callable_2
    )


def test_pickle_overridden_builtin_dataclass(create_module: Any):
    module = create_module(
        # language=Python
        """\
import dataclasses
import pydantic


@pydantic.dataclasses.dataclass(config=pydantic.config.ConfigDict(validate_assignment=True))
class BuiltInDataclassForPickle:
    value: int
        """
    )
    obj = module.BuiltInDataclassForPickle(value=5)

    pickled_obj = pickle.dumps(obj)
    restored_obj = pickle.loads(pickled_obj)

    assert restored_obj.value == 5
    assert restored_obj == obj

    # ensure the restored dataclass is still a pydantic dataclass
    with pytest.raises(ValidationError):
        restored_obj.value = 'value of a wrong type'


def lazy_cases_for_dataclass_equality_checks():
    """
    The reason for the convoluted structure of this function is to avoid
    creating the classes while collecting tests, which may trigger breakpoints
    etc. while working on one specific test.
    """
    cases = []

    def get_cases():
        if cases:
            return cases  # cases already "built"

        @dataclasses.dataclass(frozen=True)
        class StdLibFoo:
            a: str
            b: int

        @pydantic.dataclasses.dataclass(frozen=True)
        class PydanticFoo:
            a: str
            b: int

        @dataclasses.dataclass(frozen=True)
        class StdLibBar:
            c: StdLibFoo

        @pydantic.dataclasses.dataclass(frozen=True)
        class PydanticBar:
            c: PydanticFoo

        @dataclasses.dataclass(frozen=True)
        class StdLibBaz:
            c: PydanticFoo

        @pydantic.dataclasses.dataclass(frozen=True)
        class PydanticBaz:
            c: StdLibFoo

        foo = StdLibFoo(a='Foo', b=1)
        cases.append((foo, StdLibBar(c=foo)))

        foo = PydanticFoo(a='Foo', b=1)
        cases.append((foo, PydanticBar(c=foo)))

        foo = PydanticFoo(a='Foo', b=1)
        cases.append((foo, StdLibBaz(c=foo)))

        foo = StdLibFoo(a='Foo', b=1)
        cases.append((foo, PydanticBaz(c=foo)))

        return cases

    case_ids = ['stdlib_stdlib', 'pydantic_pydantic', 'pydantic_stdlib', 'stdlib_pydantic']

    def case(i):
        def get_foo_bar():
            return get_cases()[i]

        get_foo_bar.__name__ = case_ids[i]  # get nice names in pytest output
        return get_foo_bar

    return [case(i) for i in range(4)]


@pytest.mark.parametrize('foo_bar_getter', lazy_cases_for_dataclass_equality_checks())
def test_dataclass_equality_for_field_values(foo_bar_getter):
    # Related to issue #2162
    foo, bar = foo_bar_getter()
    assert dataclasses.asdict(foo) == dataclasses.asdict(bar.c)
    assert dataclasses.astuple(foo) == dataclasses.astuple(bar.c)
    assert foo == bar.c


def test_issue_2383():
    @dataclasses.dataclass
    class A:
        s: str

        def __hash__(self):
            return 123

    class B(pydantic.BaseModel):
        a: A

    a = A('')
    b = B(a=a)

    assert hash(a) == 123
    assert hash(b.a) == 123


def test_issue_2398():
    @dataclasses.dataclass(order=True)
    class DC:
        num: int = 42

    class Model(pydantic.BaseModel):
        dc: DC

    real_dc = DC()
    model = Model(dc=real_dc)

    # This works as expected.
    assert real_dc <= real_dc
    assert model.dc <= model.dc
    assert real_dc <= model.dc


def test_issue_2424():
    @dataclasses.dataclass
    class Base:
        x: str

    @dataclasses.dataclass
    class Thing(Base):
        y: str = dataclasses.field(default_factory=str)

    assert Thing(x='hi').y == ''

    @pydantic.dataclasses.dataclass
    class ValidatedThing(Base):
        y: str = dataclasses.field(default_factory=str)

    assert Thing(x='hi').y == ''
    assert ValidatedThing(x='hi').y == ''


def test_issue_2541():
    @dataclasses.dataclass(frozen=True)
    class Infos:
        id: int

    @dataclasses.dataclass(frozen=True)
    class Item:
        name: str
        infos: Infos

    class Example(BaseModel):
        item: Item

    e = Example.model_validate({'item': {'name': '123', 'infos': {'id': '1'}}})
    assert e.item.name == '123'
    assert e.item.infos.id == 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.item.infos.id = 2


def test_complex_nested_vanilla_dataclass():
    @dataclasses.dataclass
    class Span:
        first: int
        last: int

    @dataclasses.dataclass
    class LabeledSpan(Span):
        label: str

    @dataclasses.dataclass
    class BinaryRelation:
        subject: LabeledSpan
        object: LabeledSpan
        label: str

    @dataclasses.dataclass
    class Sentence:
        relations: BinaryRelation

    class M(pydantic.BaseModel):
        s: Sentence

    assert M.model_json_schema() == {
        '$defs': {
            'BinaryRelation': {
                'properties': {
                    'label': {'title': 'Label', 'type': 'string'},
                    'object': {'$ref': '#/$defs/LabeledSpan'},
                    'subject': {'$ref': '#/$defs/LabeledSpan'},
                },
                'required': ['subject', 'object', 'label'],
                'title': 'BinaryRelation',
                'type': 'object',
            },
            'LabeledSpan': {
                'properties': {
                    'first': {'title': 'First', 'type': 'integer'},
                    'label': {'title': 'Label', 'type': 'string'},
                    'last': {'title': 'Last', 'type': 'integer'},
                },
                'required': ['first', 'last', 'label'],
                'title': 'LabeledSpan',
                'type': 'object',
            },
            'Sentence': {
                'properties': {'relations': {'$ref': '#/$defs/BinaryRelation'}},
                'required': ['relations'],
                'title': 'Sentence',
                'type': 'object',
            },
        },
        'properties': {'s': {'$ref': '#/$defs/Sentence'}},
        'required': ['s'],
        'title': 'M',
        'type': 'object',
    }


def test_json_schema_with_computed_field():
    @dataclasses.dataclass
    class MyDataclass:
        x: int

        @computed_field
        @property
        def double_x(self) -> int:
            return 2 * self.x

    class Model(BaseModel):
        dc: MyDataclass

    assert Model.model_json_schema(mode='validation') == {
        '$defs': {
            'MyDataclass': {
                'properties': {'x': {'title': 'X', 'type': 'integer'}},
                'required': ['x'],
                'title': 'MyDataclass',
                'type': 'object',
            }
        },
        'properties': {'dc': {'$ref': '#/$defs/MyDataclass'}},
        'required': ['dc'],
        'title': 'Model',
        'type': 'object',
    }
    assert Model.model_json_schema(mode='serialization') == {
        '$defs': {
            'MyDataclass': {
                'properties': {
                    'double_x': {'readOnly': True, 'title': 'Double X', 'type': 'integer'},
                    'x': {'title': 'X', 'type': 'integer'},
                },
                'required': ['x', 'double_x'],
                'title': 'MyDataclass',
                'type': 'object',
            }
        },
        'properties': {'dc': {'$ref': '#/$defs/MyDataclass'}},
        'required': ['dc'],
        'title': 'Model',
        'type': 'object',
    }


def test_issue_2594():
    @dataclasses.dataclass
    class Empty:
        pass

    @pydantic.dataclasses.dataclass
    class M:
        e: Empty

    assert isinstance(M(e={}).e, Empty)


def test_schema_description_unset():
    @pydantic.dataclasses.dataclass
    class A:
        x: int

    assert 'description' not in model_json_schema(A)

    @pydantic.dataclasses.dataclass
    @dataclasses.dataclass
    class B:
        x: int

    assert 'description' not in model_json_schema(B)


def test_schema_description_set():
    @pydantic.dataclasses.dataclass
    class A:
        """my description"""

        x: int

    assert model_json_schema(A)['description'] == 'my description'

    @pydantic.dataclasses.dataclass
    @dataclasses.dataclass
    class B:
        """my description"""

        x: int

    assert model_json_schema(A)['description'] == 'my description'


def test_issue_3011():
    """Validation of a subclass of a dataclass"""

    @dataclasses.dataclass
    class A:
        thing_a: str

    class B(A):
        thing_b: str

    @pydantic.dataclasses.dataclass
    class C:
        thing: A

    b = B('Thing A')
    c = C(thing=b)
    assert c.thing.thing_a == 'Thing A'


def test_issue_3162():
    @dataclasses.dataclass
    class User:
        id: int
        name: str

    class Users(BaseModel):
        user: User
        other_user: User

    assert Users.model_json_schema() == {
        '$defs': {
            'User': {
                'properties': {'id': {'title': 'Id', 'type': 'integer'}, 'name': {'title': 'Name', 'type': 'string'}},
                'required': ['id', 'name'],
                'title': 'User',
                'type': 'object',
            }
        },
        'properties': {'other_user': {'$ref': '#/$defs/User'}, 'user': {'$ref': '#/$defs/User'}},
        'required': ['user', 'other_user'],
        'title': 'Users',
        'type': 'object',
    }


def test_discriminated_union_basemodel_instance_value():
    @pydantic.dataclasses.dataclass
    class A:
        l: Literal['a']  # noqa: E741

    @pydantic.dataclasses.dataclass
    class B:
        l: Literal['b']  # noqa: E741

    @pydantic.dataclasses.dataclass
    class Top:
        sub: Union[A, B] = dataclasses.field(metadata=dict(discriminator='l'))

    t = Top(sub=A(l='a'))
    assert isinstance(t, Top)
    # insert_assert(model_json_schema(Top))
    assert model_json_schema(Top) == {
        'title': 'Top',
        'type': 'object',
        'properties': {
            'sub': {
                'title': 'Sub',
                'discriminator': {'mapping': {'a': '#/$defs/A', 'b': '#/$defs/B'}, 'propertyName': 'l'},
                'oneOf': [{'$ref': '#/$defs/A'}, {'$ref': '#/$defs/B'}],
            }
        },
        'required': ['sub'],
        '$defs': {
            'A': {
                'properties': {'l': {'const': 'a', 'enum': ['a'], 'title': 'L', 'type': 'string'}},
                'required': ['l'],
                'title': 'A',
                'type': 'object',
            },
            'B': {
                'properties': {'l': {'const': 'b', 'enum': ['b'], 'title': 'L', 'type': 'string'}},
                'required': ['l'],
                'title': 'B',
                'type': 'object',
            },
        },
    }


def test_post_init_after_validation():
    @dataclasses.dataclass
    class SetWrapper:
        set: Set[int]

        def __post_init__(self):
            assert isinstance(
                self.set, set
            ), f"self.set should be a set but it's {self.set!r} of type {type(self.set).__name__}"

    class Model(pydantic.BaseModel):
        set_wrapper: SetWrapper

    model = Model(set_wrapper=SetWrapper({1, 2, 3}))
    json_text = model.model_dump_json()
    assert Model.model_validate_json(json_text).model_dump() == model.model_dump()


def test_new_not_called():
    """
    pydantic dataclasses do not preserve sunder attributes set in __new__
    """

    class StandardClass:
        """Class which modifies instance creation."""

        a: str

        def __new__(cls, *args, **kwargs):
            instance = super().__new__(cls)

            instance._special_property = 1

            return instance

    StandardLibDataclass = dataclasses.dataclass(StandardClass)
    PydanticDataclass = pydantic.dataclasses.dataclass(StandardClass)

    test_string = 'string'

    std_instance = StandardLibDataclass(a=test_string)
    assert std_instance._special_property == 1
    assert std_instance.a == test_string

    pyd_instance = PydanticDataclass(a=test_string)
    assert not hasattr(pyd_instance, '_special_property')
    assert pyd_instance.a == test_string


def test_ignore_extra():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='ignore'))
    class Foo:
        x: int

    foo = Foo(**{'x': '1', 'y': '2'})
    assert foo.__dict__ == {'x': 1}


def test_ignore_extra_subclass():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='ignore'))
    class Foo:
        x: int

    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='ignore'))
    class Bar(Foo):
        y: int

    bar = Bar(**{'x': '1', 'y': '2', 'z': '3'})
    assert bar.__dict__ == {'x': 1, 'y': 2}


def test_allow_extra():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='allow'))
    class Foo:
        x: int

    foo = Foo(**{'x': '1', 'y': '2'})
    assert foo.__dict__ == {'x': 1, 'y': '2'}


def test_allow_extra_subclass():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='allow'))
    class Foo:
        x: int

    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='allow'))
    class Bar(Foo):
        y: int

    bar = Bar(**{'x': '1', 'y': '2', 'z': '3'})
    assert bar.__dict__ == {'x': 1, 'y': 2, 'z': '3'}


def test_forbid_extra():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='forbid'))
    class Foo:
        x: int

    msg = re.escape("Unexpected keyword argument [type=unexpected_keyword_argument, input_value='2', input_type=str]")

    with pytest.raises(ValidationError, match=msg):
        Foo(**{'x': '1', 'y': '2'})


def test_self_reference_dataclass():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        self_reference: Optional['MyDataclass'] = None

    assert MyDataclass.__pydantic_fields__['self_reference'].annotation == Optional[MyDataclass]

    instance = MyDataclass(self_reference=MyDataclass(self_reference=MyDataclass()))
    assert TypeAdapter(MyDataclass).dump_python(instance) == {
        'self_reference': {'self_reference': {'self_reference': None}}
    }

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(self_reference=1)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dataclass_type',
            'loc': ('self_reference',),
            'msg': 'Input should be a dictionary or an instance of MyDataclass',
            'input': 1,
            'ctx': {'class_name': 'MyDataclass'},
        }
    ]


def test_cyclic_reference_dataclass(create_module):
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='forbid'))
    class D1:
        d2: Optional['D2'] = None

    @create_module
    def module():
        from typing import Optional

        import pydantic

        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(extra='forbid'))
        class D2:
            d1: Optional['D1'] = None

    # Ensure D2 is in the local namespace; note everything works even though it wasn't _defined_ in this namespace
    D2 = module.D2

    # Confirm D1 and D2 require rebuilding
    assert isinstance(D1.__pydantic_validator__, MockValSer)
    assert isinstance(D2.__pydantic_validator__, MockValSer)

    # Note: the rebuilds of D1 and D2 happen automatically, and works since it grabs the locals here as the namespace,
    # which contains D1 and D2
    instance = D1(d2=D2(d1=D1(d2=D2(d1=D1()))))

    # Confirm D1 and D2 have been rebuilt
    assert isinstance(D1.__pydantic_validator__, SchemaValidator)
    assert isinstance(D2.__pydantic_validator__, SchemaValidator)

    assert TypeAdapter(D1).dump_python(instance) == {'d2': {'d1': {'d2': {'d1': {'d2': None}}}}}

    with pytest.raises(ValidationError) as exc_info:
        D2(d1=D2())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dataclass_type',
            'loc': ('d1',),
            'msg': 'Input should be a dictionary or an instance of D1',
            'input': D2(d1=None),
            'ctx': {'class_name': 'D1'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(D1).validate_python(dict(d2=dict(d1=dict(d2=dict(d2=dict())))))
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': {},
            'loc': ('d2', 'd1', 'd2', 'd2'),
            'msg': 'Unexpected keyword argument',
            'type': 'unexpected_keyword_argument',
        }
    ]


def test_cross_module_cyclic_reference_dataclass(create_module):
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='forbid'))
    class D1:
        d2: Optional['D2'] = None  # noqa F821

    @create_module
    def module():
        from typing import Optional

        import pydantic

        @pydantic.dataclasses.dataclass(config=pydantic.ConfigDict(extra='forbid'))
        class D2:
            d1: Optional['D1'] = None

    # Since D2 is not in locals, it will not be picked up by the auto-rebuild:
    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            '`D1` is not fully defined; you should define `D2`, then call'
            ' `pydantic.dataclasses.rebuild_dataclass(D1)`.'
        ),
    ):
        D1()

    # Explicitly rebuild D1, specifying the appropriate types namespace
    rebuild_dataclass(D1, _types_namespace={'D2': module.D2, 'D1': D1})

    # Confirm D2 still requires a rebuild (it will happen automatically)
    assert isinstance(module.D2.__pydantic_validator__, MockValSer)

    instance = D1(d2=module.D2(d1=D1(d2=module.D2(d1=D1()))))

    # Confirm auto-rebuild of D2 has now happened
    assert isinstance(module.D2.__pydantic_validator__, SchemaValidator)

    assert TypeAdapter(D1).dump_python(instance) == {'d2': {'d1': {'d2': {'d1': {'d2': None}}}}}

    with pytest.raises(ValidationError) as exc_info:
        module.D2(d1=module.D2())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dataclass_type',
            'input': module.D2(d1=None),
            'loc': ('d1',),
            'msg': 'Input should be a dictionary or an instance of D1',
            'ctx': {'class_name': 'D1'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(D1).validate_python(dict(d2=dict(d1=dict(d2=dict(d2=dict())))))
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': {},
            'loc': ('d2', 'd1', 'd2', 'd2'),
            'msg': 'Unexpected keyword argument',
            'type': 'unexpected_keyword_argument',
        }
    ]


@pytest.mark.parametrize(
    'dataclass_decorator',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
def test_base_dataclasses_annotations_resolving(create_module, dataclass_decorator: Callable):
    @create_module
    def module():
        import dataclasses
        from typing import NewType

        OddInt = NewType('OddInt', int)

        @dataclasses.dataclass
        class D1:
            d1: 'OddInt'
            s: str

            __pydantic_config__ = {'str_to_lower': True}

    @dataclass_decorator
    class D2(module.D1):
        d2: int

    assert TypeAdapter(D2).validate_python({'d1': 1, 'd2': 2, 's': 'ABC'}) == D2(d1=1, d2=2, s='abc')


@pytest.mark.parametrize(
    'dataclass_decorator',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
def test_base_dataclasses_annotations_resolving_with_override(create_module, dataclass_decorator: Callable):
    @create_module
    def module1():
        import dataclasses
        from typing import NewType

        IDType = NewType('IDType', int)

        @dataclasses.dataclass
        class D1:
            db_id: 'IDType'

            __pydantic_config__ = {'str_to_lower': True}

    @create_module
    def module2():
        import dataclasses
        from typing import NewType

        IDType = NewType('IDType', str)

        @dataclasses.dataclass
        class D2:
            db_id: 'IDType'
            s: str

            __pydantic_config__ = {'str_to_lower': False}

    @dataclass_decorator
    class D3(module1.D1, module2.D2): ...

    assert TypeAdapter(D3).validate_python({'db_id': 42, 's': 'ABC'}) == D3(db_id=42, s='abc')


@pytest.mark.skipif(sys.version_info < (3, 10), reason='kw_only is not available in python < 3.10')
def test_kw_only():
    @pydantic.dataclasses.dataclass(kw_only=True)
    class A:
        a: int | None = None
        b: str

    with pytest.raises(ValidationError):
        A(1, '')

    assert A(b='hi').b == 'hi'


@pytest.mark.skipif(sys.version_info < (3, 10), reason='kw_only is not available in python < 3.10')
def test_kw_only_subclass():
    @pydantic.dataclasses.dataclass
    class A:
        x: int
        y: int = pydantic.Field(default=0, kw_only=True)

    @pydantic.dataclasses.dataclass
    class B(A):
        z: int

    assert B(1, 2) == B(x=1, y=0, z=2)
    assert B(1, y=2, z=3) == B(x=1, y=2, z=3)


@pytest.mark.parametrize('field_constructor', [pydantic.dataclasses.Field, dataclasses.field])
def test_repr_false(field_constructor: Callable):
    @pydantic.dataclasses.dataclass
    class A:
        visible_field: str
        hidden_field: str = field_constructor(repr=False)

    instance = A(visible_field='this_should_be_included', hidden_field='this_should_not_be_included')
    assert "visible_field='this_should_be_included'" in repr(instance)
    assert "hidden_field='this_should_not_be_included'" not in repr(instance)


def dataclass_decorators(include_identity: bool = False, exclude_combined: bool = False):
    decorators = [pydantic.dataclasses.dataclass, dataclasses.dataclass]
    ids = ['pydantic', 'stdlib']

    if not exclude_combined:

        def combined_decorator(cls):
            """
            Should be equivalent to:
            @pydantic.dataclasses.dataclass
            @dataclasses.dataclass
            """
            return pydantic.dataclasses.dataclass(dataclasses.dataclass(cls))

        decorators.append(combined_decorator)
        ids.append('combined')

    if include_identity:

        def identity_decorator(cls):
            return cls

        decorators.append(identity_decorator)
        ids.append('identity')

    return {'argvalues': decorators, 'ids': ids}


@pytest.mark.skipif(sys.version_info < (3, 10), reason='kw_only is not available in python < 3.10')
@pytest.mark.parametrize('decorator1', **dataclass_decorators(exclude_combined=True))
@pytest.mark.parametrize('decorator2', **dataclass_decorators(exclude_combined=True))
def test_kw_only_inheritance(decorator1, decorator2):
    # Exclude combined from the decorators since it doesn't know how to accept kw_only
    @decorator1(kw_only=True)
    class Parent:
        x: int

    @decorator2
    class Child(Parent):
        y: int

    child = Child(1, x=2)
    assert child.x == 2
    assert child.y == 1


def test_extra_forbid_list_no_error():
    @pydantic.dataclasses.dataclass(config=dict(extra='forbid'))
    class Bar: ...

    @pydantic.dataclasses.dataclass
    class Foo:
        a: List[Bar]

    assert isinstance(Foo(a=[Bar()]).a[0], Bar)


def test_extra_forbid_list_error():
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra='forbid'))
    class Bar: ...

    with pytest.raises(ValidationError, match=r'a\s+Unexpected keyword argument'):
        Bar(a=1)


def test_field_validator():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: float

        @field_validator('b')
        @classmethod
        def double_b(cls, v):
            return v * 2

    d = MyDataclass('1', '2.5')
    assert d.a == 1
    assert d.b == 5.0


def test_model_validator_before():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: float

        @model_validator(mode='before')
        @classmethod
        def double_b(cls, v: ArgsKwargs):
            v.kwargs['b'] *= 2
            return v

    d = MyDataclass('1', b='2')
    assert d.a == 1
    assert d.b == 22.0


def test_model_validator_after():
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        a: int
        b: float

        @model_validator(mode='after')
        def double_b(self) -> 'MyDataclass':
            self.b *= 2
            return self

    d = MyDataclass('1', b='2')
    assert d.a == 1
    assert d.b == 4


def test_parent_post_init():
    """
    Test that the parent's __post_init__ gets called
    and the order in which it gets called relative to validation.

    In V1 we called it before validation, in V2 it gets called after.
    """

    @dataclasses.dataclass
    class A:
        a: float

        def __post_init__(self):
            self.a *= 2

    assert A(a=1.2).a == 2.4

    @pydantic.dataclasses.dataclass
    class B(A):
        @field_validator('a')
        @classmethod
        def validate_a(cls, value, _):
            value += 3
            return value

    assert B(a=1).a == 8  # (1 + 3) * 2 = 8


def test_subclass_post_init_order():
    @dataclasses.dataclass
    class A:
        a: float

    @pydantic.dataclasses.dataclass
    class B(A):
        def __post_init__(self):
            self.a *= 2

        @field_validator('a')
        @classmethod
        def validate_a(cls, value):
            value += 3
            return value

    assert B(a=1).a == 8  # (1 + 3) * 2 = 8


def test_subclass_post_init_inheritance():
    @dataclasses.dataclass
    class A:
        a: int

    @pydantic.dataclasses.dataclass
    class B(A):
        def __post_init__(self):
            self.a *= 2

        @field_validator('a')
        @classmethod
        def validate_a(cls, value):
            value += 3
            return value

    @pydantic.dataclasses.dataclass
    class C(B):
        def __post_init__(self):
            self.a *= 3

    assert C(1).a == 12  # (1 + 3) * 3


def test_config_as_type_deprecated():
    class Config:
        validate_assignment = True

    with pytest.warns(
        PydanticDeprecatedSince20, match='Support for class-based `config` is deprecated, use ConfigDict instead.'
    ):

        @pydantic.dataclasses.dataclass(config=Config)
        class MyDataclass:
            a: int

    assert MyDataclass.__pydantic_config__ == ConfigDict(validate_assignment=True)


def test_validator_info_field_name_data_before():
    """
    Test accessing info.field_name and info.data
    We only test the `before` validator because they
    all share the same implementation.
    """

    @pydantic.dataclasses.dataclass
    class Model:
        a: str
        b: str

        @field_validator('b', mode='before')
        @classmethod
        def check_a(cls, v: Any, info: ValidationInfo) -> Any:
            assert v == b'but my barbaz is better'
            assert info.field_name == 'b'
            assert info.data == {'a': 'your foobar is good'}
            return 'just kidding!'

    assert Model(a=b'your foobar is good', b=b'but my barbaz is better').b == 'just kidding!'


@pytest.mark.parametrize(
    'decorator1, expected_parent, expected_child',
    [
        (
            pydantic.dataclasses.dataclass,
            ['parent before', 'parent', 'parent after'],
            ['parent before', 'child', 'parent after', 'child before', 'child after'],
        ),
        (dataclasses.dataclass, [], ['parent before', 'child', 'parent after', 'child before', 'child after']),
    ],
    ids=['pydantic', 'stdlib'],
)
def test_inheritance_replace(decorator1: Callable[[Any], Any], expected_parent: List[str], expected_child: List[str]):
    """We promise that if you add a validator
    with the same _function_ name as an existing validator
    it replaces the existing validator and is run instead of it.
    """

    @decorator1
    class Parent:
        a: List[str]

        @field_validator('a')
        @classmethod
        def parent_val_before(cls, v: List[str]):
            v.append('parent before')
            return v

        @field_validator('a')
        @classmethod
        def val(cls, v: List[str]):
            v.append('parent')
            return v

        @field_validator('a')
        @classmethod
        def parent_val_after(cls, v: List[str]):
            v.append('parent after')
            return v

    @pydantic.dataclasses.dataclass
    class Child(Parent):
        @field_validator('a')
        @classmethod
        def child_val_before(cls, v: List[str]):
            v.append('child before')
            return v

        @field_validator('a')
        @classmethod
        def val(cls, v: List[str]):
            v.append('child')
            return v

        @field_validator('a')
        @classmethod
        def child_val_after(cls, v: List[str]):
            v.append('child after')
            return v

    assert Parent(a=[]).a == expected_parent
    assert Child(a=[]).a == expected_child


@pytest.mark.parametrize(
    'decorator1',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
@pytest.mark.parametrize(
    'default',
    [1, dataclasses.field(default=1), Field(default=1)],
    ids=['1', 'dataclasses.field(default=1)', 'pydantic.Field(default=1)'],
)
def test_dataclasses_inheritance_default_value_is_not_deleted(
    decorator1: Callable[[Any], Any], default: Literal[1]
) -> None:
    if decorator1 is dataclasses.dataclass and isinstance(default, FieldInfo):
        pytest.skip(reason="stdlib dataclasses don't support Pydantic fields")

    @decorator1
    class Parent:
        a: int = default

    assert Parent.a == 1
    assert Parent().a == 1

    @pydantic.dataclasses.dataclass
    class Child(Parent):
        pass

    assert Child.a == 1
    assert Child().a == 1


def test_dataclass_config_validate_default():
    @pydantic.dataclasses.dataclass
    class Model:
        x: int = -1

        @field_validator('x')
        @classmethod
        def force_x_positive(cls, v):
            assert v > 0
            return v

    assert Model().x == -1

    @pydantic.dataclasses.dataclass(config=ConfigDict(validate_default=True))
    class ValidatingModel(Model):
        pass

    with pytest.raises(ValidationError) as exc_info:
        ValidatingModel()
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'error': HasRepr(repr(AssertionError('assert -1 > 0')))},
            'input': -1,
            'loc': ('x',),
            'msg': 'Assertion failed, assert -1 > 0',
            'type': 'assertion_error',
        }
    ]


@pytest.mark.parametrize('dataclass_decorator', **dataclass_decorators())
def test_unparametrized_generic_dataclass(dataclass_decorator):
    T = TypeVar('T')

    @dataclass_decorator
    class GenericDataclass(Generic[T]):
        x: T

    # In principle we could call GenericDataclass(...) below, but this won't do validation
    # for standard dataclasses, so we just use TypeAdapter to get validation for each.
    validator = pydantic.TypeAdapter(GenericDataclass)

    assert validator.validate_python({'x': None}).x is None
    assert validator.validate_python({'x': 1}).x == 1

    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python({'y': None})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'y': None}, 'loc': ('x',), 'msg': 'Field required', 'type': 'missing'}
    ]


@pytest.mark.parametrize('dataclass_decorator', **dataclass_decorators())
@pytest.mark.parametrize(
    'annotation,input_value,error,output_value',
    [
        (int, 1, False, 1),
        (str, 'a', False, 'a'),
        (
            int,
            'a',
            True,
            [
                {
                    'input': 'a',
                    'loc': ('x',),
                    'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
                    'type': 'int_parsing',
                }
            ],
        ),
    ],
)
def test_parametrized_generic_dataclass(dataclass_decorator, annotation, input_value, error, output_value):
    T = TypeVar('T')

    @dataclass_decorator
    class GenericDataclass(Generic[T]):
        x: T

    # Need to use TypeAdapter here because GenericDataclass[annotation] will be a GenericAlias, which delegates
    # method calls to the (non-parametrized) origin class. This is essentially a limitation of typing._GenericAlias.
    validator = pydantic.TypeAdapter(GenericDataclass[annotation])

    if not error:
        assert validator.validate_python({'x': input_value}).x == output_value
    else:
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_python({'x': input_value})
        assert exc_info.value.errors(include_url=False) == output_value


def test_multiple_parametrized_generic_dataclasses():
    T = TypeVar('T')

    @pydantic.dataclasses.dataclass
    class GenericDataclass(Generic[T]):
        x: T

    validator1 = pydantic.TypeAdapter(GenericDataclass[int])
    validator2 = pydantic.TypeAdapter(GenericDataclass[str])

    # verify that generic parameters are showing up in the type ref for generic dataclasses
    # this can probably be removed if the schema changes in some way that makes this part of the test fail
    assert '[int:' in validator1.core_schema['ref']
    assert '[str:' in validator2.core_schema['ref']

    assert validator1.validate_python({'x': 1}).x == 1
    assert validator2.validate_python({'x': 'hello world'}).x == 'hello world'

    with pytest.raises(ValidationError) as exc_info:
        validator2.validate_python({'x': 1})
    assert exc_info.value.errors(include_url=False) == [
        {'input': 1, 'loc': ('x',), 'msg': 'Input should be a valid string', 'type': 'string_type'}
    ]
    with pytest.raises(ValidationError) as exc_info:
        validator1.validate_python({'x': 'hello world'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'hello world',
            'loc': ('x',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


@pytest.mark.parametrize('dataclass_decorator', **dataclass_decorators(include_identity=True))
def test_pydantic_dataclass_preserves_metadata(dataclass_decorator: Callable[[Any], Any]) -> None:
    @dataclass_decorator
    class FooStd:
        """Docstring"""

    FooPydantic = pydantic.dataclasses.dataclass(FooStd)

    assert FooPydantic.__module__ == FooStd.__module__
    assert FooPydantic.__name__ == FooStd.__name__
    assert FooPydantic.__qualname__ == FooStd.__qualname__


def test_recursive_dataclasses_gh_4509(create_module) -> None:
    @create_module
    def module():
        import dataclasses
        from typing import List

        import pydantic

        @dataclasses.dataclass
        class Recipe:
            author: 'Cook'

        @dataclasses.dataclass
        class Cook:
            recipes: List[Recipe]

        @pydantic.dataclasses.dataclass
        class Foo(Cook):
            pass

    gordon = module.Cook([])

    burger = module.Recipe(author=gordon)

    me = module.Foo([burger])

    assert me.recipes == [burger]


def test_dataclass_alias_generator():
    def alias_generator(name: str) -> str:
        return 'alias_' + name

    @pydantic.dataclasses.dataclass(config=ConfigDict(alias_generator=alias_generator))
    class User:
        name: str
        score: int = Field(alias='my_score')

    user = User(**{'alias_name': 'test name', 'my_score': 2})
    assert user.name == 'test name'
    assert user.score == 2

    with pytest.raises(ValidationError) as exc_info:
        User(name='test name', score=2)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('alias_name',),
            'msg': 'Field required',
            'input': ArgsKwargs((), {'name': 'test name', 'score': 2}),
        },
        {
            'type': 'missing',
            'loc': ('my_score',),
            'msg': 'Field required',
            'input': ArgsKwargs((), {'name': 'test name', 'score': 2}),
        },
    ]


def test_init_vars_inheritance():
    init_vars = []

    @pydantic.dataclasses.dataclass
    class Foo:
        init: 'InitVar[int]'

    @pydantic.dataclasses.dataclass
    class Bar(Foo):
        arg: int

        def __post_init__(self, init: int) -> None:
            init_vars.append(init)

    bar = Bar(init=1, arg=2)
    assert TypeAdapter(Bar).dump_python(bar) == {'arg': 2}
    assert init_vars == [1]

    with pytest.raises(ValidationError) as exc_info:
        Bar(init='a', arg=2)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('init',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


@pytest.mark.skipif(not hasattr(pydantic.dataclasses, '_call_initvar'), reason='InitVar was not modified')
@pytest.mark.parametrize('remove_monkeypatch', [True, False])
def test_init_vars_call_monkeypatch(remove_monkeypatch, monkeypatch):
    # Parametrizing like this allows us to test that the behavior is the same with or without the monkeypatch

    if remove_monkeypatch:
        monkeypatch.delattr(InitVar, '__call__')

    InitVar(int)  # this is what is produced by InitVar[int]; note monkeypatching __call__ doesn't break this

    with pytest.raises(TypeError, match="'InitVar' object is not callable") as exc:
        InitVar[int]()

    # Check that the custom __call__ was called precisely if the monkeypatch was not removed
    stack_depth = len(traceback.extract_tb(exc.value.__traceback__))
    assert stack_depth == 1 if remove_monkeypatch else 2


@pytest.mark.parametrize('decorator1', **dataclass_decorators())
@pytest.mark.parametrize('decorator2', **dataclass_decorators())
def test_decorators_in_model_field(decorator1, decorator2):
    @decorator1
    class Demo1:
        int1: int

        @field_validator('int1', mode='before')
        def set_int_1(cls, v):
            return v + 100

        @field_serializer('int1')
        def serialize_int_1(self, v):
            return v + 10

    @decorator2
    class Demo2(Demo1):
        int2: int

        @field_validator('int2', mode='before')
        def set_int_2(cls, v):
            return v + 200

        @field_serializer('int2')
        def serialize_int_2(self, v):
            return v + 20

    class Model(BaseModel):
        x: Demo2

    m = Model.model_validate(dict(x=dict(int1=1, int2=2)))
    assert m.x.int1 == 101
    assert m.x.int2 == 202

    assert m.model_dump() == {'x': {'int1': 111, 'int2': 222}}


@pytest.mark.parametrize('decorator1', **dataclass_decorators())
@pytest.mark.parametrize('decorator2', **dataclass_decorators())
def test_vanilla_dataclass_decorators_in_type_adapter(decorator1, decorator2):
    @decorator1
    class Demo1:
        int1: int

        @field_validator('int1', mode='before')
        def set_int_1(cls, v):
            return v + 100

        @field_serializer('int1')
        def serialize_int_1(self, v):
            return v + 10

    @decorator2
    class Demo2(Demo1):
        int2: int

        @field_validator('int2', mode='before')
        def set_int_2(cls, v):
            return v + 200

        @field_serializer('int2')
        def serialize_int_2(self, v):
            return v + 20

    adapter = TypeAdapter(Demo2)

    m = adapter.validate_python(dict(int1=1, int2=2))
    assert m.int1 == 101
    assert m.int2 == 202

    assert adapter.dump_python(m) == {'int1': 111, 'int2': 222}


@pytest.mark.parametrize(
    'dataclass_decorator',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_dataclass_slots(dataclass_decorator):
    @dataclass_decorator(slots=True)
    class Model:
        a: str
        b: str

    dc = TypeAdapter(Model).validate_python({'a': 'foo', 'b': 'bar'})
    assert dc.a == 'foo'
    assert dc.b == 'bar'


@pytest.mark.parametrize(
    'dataclass_decorator',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
@pytest.mark.skipif(sys.version_info < (3, 10), reason='slots are only supported for dataclasses in Python >= 3.10')
def test_dataclass_slots_mixed(dataclass_decorator):
    @dataclass_decorator(slots=True)
    class Model:
        x: int
        y: dataclasses.InitVar[str]
        z: ClassVar[str] = 'z-classvar'

    @dataclass_decorator
    class SubModel(Model):
        x2: int
        y2: dataclasses.InitVar[str]
        z2: ClassVar[str] = 'z2-classvar'

    dc = TypeAdapter(SubModel).validate_python({'x': 1, 'y': 'a', 'x2': 2, 'y2': 'b'})
    assert dc.x == 1
    assert dc.x2 == 2
    assert SubModel.z == 'z-classvar'
    assert SubModel.z2 == 'z2-classvar'


def test_rebuild_dataclass():
    @pydantic.dataclasses.dataclass
    class MyDataClass:
        x: str

    assert rebuild_dataclass(MyDataClass) is None

    @pydantic.dataclasses.dataclass()
    class MyDataClass1:
        d2: Optional['Foo'] = None  # noqa F821

    with pytest.raises(PydanticUndefinedAnnotation, match="name 'Foo' is not defined"):
        rebuild_dataclass(MyDataClass1, _parent_namespace_depth=0)


@pytest.mark.parametrize(
    'dataclass_decorator',
    [
        pydantic.dataclasses.dataclass,
        dataclasses.dataclass,
    ],
    ids=['pydantic', 'stdlib'],
)
def test_model_config(dataclass_decorator: Any) -> None:
    @dataclass_decorator
    class Model:
        x: str
        __pydantic_config__ = ConfigDict(str_to_lower=True)

    ta = TypeAdapter(Model)
    assert ta.validate_python({'x': 'ABC'}).x == 'abc'


def test_model_config_override_in_decorator() -> None:
    @pydantic.dataclasses.dataclass(config=ConfigDict(str_to_lower=False, str_strip_whitespace=True))
    class Model:
        x: str
        __pydantic_config__ = ConfigDict(str_to_lower=True)

    ta = TypeAdapter(Model)
    assert ta.validate_python({'x': 'ABC '}).x == 'ABC'


def test_model_config_override_in_decorator_empty_config() -> None:
    @pydantic.dataclasses.dataclass(config=ConfigDict())
    class Model:
        x: str
        __pydantic_config__ = ConfigDict(str_to_lower=True)

    ta = TypeAdapter(Model)
    assert ta.validate_python({'x': 'ABC '}).x == 'ABC '


def test_dataclasses_with_config_decorator():
    @dataclasses.dataclass
    @with_config(ConfigDict(str_to_lower=True))
    class Model1:
        x: str

    ta = TypeAdapter(Model1)
    assert ta.validate_python({'x': 'ABC'}).x == 'abc'

    @with_config(ConfigDict(str_to_lower=True))
    @dataclasses.dataclass
    class Model2:
        x: str

    ta = TypeAdapter(Model2)
    assert ta.validate_python({'x': 'ABC'}).x == 'abc'


def test_pydantic_field_annotation():
    @pydantic.dataclasses.dataclass
    class Model:
        x: Annotated[int, Field(gt=0)]

    with pytest.raises(ValidationError) as exc_info:
        Model(x=-1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'gt': 0},
            'input': -1,
            'loc': ('x',),
            'msg': 'Input should be greater than 0',
            'type': 'greater_than',
        }
    ]


def test_combined_field_annotations():
    """
    This test is included to document the fact that `Field` and `field` can be used together.
    That said, if you mix them like this, there is a good chance you'll run into surprising behavior/bugs.

    (E.g., `x: Annotated[int, Field(gt=1, validate_default=True)] = field(default=0)` doesn't cause an error)

    I would generally advise against doing this, and if we do change the behavior in the future to somehow merge
    pydantic.FieldInfo and dataclasses.Field in a way that changes runtime behavior for existing code, I would probably
    consider it a bugfix rather than a breaking change.
    """

    @pydantic.dataclasses.dataclass
    class Model:
        x: Annotated[int, Field(gt=1)] = dataclasses.field(default=1)

    assert Model().x == 1

    with pytest.raises(ValidationError) as exc_info:
        Model(x=0)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'gt': 1},
            'input': 0,
            'loc': ('x',),
            'msg': 'Input should be greater than 1',
            'type': 'greater_than',
        }
    ]


def test_dataclass_field_default_factory_with_init():
    @pydantic.dataclasses.dataclass
    class Model:
        x: int = dataclasses.field(default_factory=lambda: 3, init=False)

    m = Model()
    assert 'x' in Model.__pydantic_fields__
    assert m.x == 3
    assert RootModel[Model](m).model_dump() == {'x': 3}


def test_dataclass_field_default_with_init():
    @pydantic.dataclasses.dataclass
    class Model:
        x: int = dataclasses.field(default=3, init=False)

    m = Model()
    assert 'x' in Model.__pydantic_fields__
    assert m.x == 3
    assert RootModel[Model](m).model_dump() == {'x': 3}


def test_metadata():
    @dataclasses.dataclass
    class Test:
        value: int = dataclasses.field(metadata={'info': 'Some int value', 'json_schema_extra': {'a': 'b'}})

    PydanticTest = pydantic.dataclasses.dataclass(Test)

    assert TypeAdapter(PydanticTest).json_schema() == {
        'properties': {'value': {'a': 'b', 'title': 'Value', 'type': 'integer'}},
        'required': ['value'],
        'title': 'Test',
        'type': 'object',
    }


def test_signature():
    @pydantic.dataclasses.dataclass
    class Model:
        x: int
        y: str = 'y'
        z: float = dataclasses.field(default=1.0)
        a: float = dataclasses.field(default_factory=float)
        b: float = Field(default=1.0)
        c: float = Field(default_factory=float)
        d: int = dataclasses.field(metadata={'alias': 'dd'}, default=1)

    assert str(inspect.signature(Model)) == (
        "(x: int, y: str = 'y', z: float = 1.0, a: float = <factory>, b: float = 1.0, c: float = <factory>, dd: int = 1) -> None"
    )


def test_inherited_dataclass_signature():
    @pydantic.dataclasses.dataclass
    class A:
        a: int

    @pydantic.dataclasses.dataclass
    class B(A):
        b: int

    assert str(inspect.signature(A)) == '(a: int) -> None'
    assert str(inspect.signature(B)) == '(a: int, b: int) -> None'


def test_dataclasses_with_slots_and_default():
    @pydantic.dataclasses.dataclass(slots=True)
    class A:
        a: int = 0

    assert A().a == 0

    @pydantic.dataclasses.dataclass(slots=True)
    class B:
        b: int = Field(1)

    assert B().b == 1


def test_schema_generator() -> None:
    class LaxStrGenerator(GenerateSchema):
        def str_schema(self) -> CoreSchema:
            return core_schema.no_info_plain_validator_function(str)

    @pydantic.dataclasses.dataclass
    class Model:
        x: str
        __pydantic_config__ = ConfigDict(schema_generator=LaxStrGenerator)

    assert Model(x=1).x == '1'


@pytest.mark.parametrize('decorator1', **dataclass_decorators())
def test_annotated_before_validator_called_once(decorator1):
    count = 0

    def convert(value: int) -> str:
        nonlocal count
        count += 1
        return str(value)

    IntToStr = Annotated[str, BeforeValidator(convert)]

    @decorator1
    class A:
        a: IntToStr

    assert count == 0
    TypeAdapter(A).validate_python({'a': 123})
    assert count == 1


def test_is_pydantic_dataclass():
    @pydantic.dataclasses.dataclass
    class PydanticDataclass:
        a: int

    @dataclasses.dataclass
    class StdLibDataclass:
        b: int

    assert is_pydantic_dataclass(PydanticDataclass) is True
    assert is_pydantic_dataclass(StdLibDataclass) is False


def test_can_inherit_stdlib_dataclasses_with_defaults():
    @dataclasses.dataclass
    class Base:
        a: None = None

    class Model(BaseModel, Base):
        pass

    assert Model().a is None


def test_can_inherit_stdlib_dataclasses_default_factories_and_use_them():
    """This test documents that default factories are not supported"""

    @dataclasses.dataclass
    class Base:
        a: str = dataclasses.field(default_factory=lambda: 'TEST')

    class Model(BaseModel, Base):
        pass

    with pytest.raises(ValidationError):
        assert Model().a == 'TEST'


def test_can_inherit_stdlib_dataclasses_default_factories_and_provide_a_value():
    @dataclasses.dataclass
    class Base:
        a: str = dataclasses.field(default_factory=lambda: 'TEST')

    class Model(BaseModel, Base):
        pass

    assert Model(a='NOT_THE_SAME').a == 'NOT_THE_SAME'


def test_can_inherit_stdlib_dataclasses_with_dataclass_fields():
    @dataclasses.dataclass
    class Base:
        a: int = dataclasses.field(default=5)

    class Model(BaseModel, Base):
        pass

    assert Model().a == 5


def test_alias_with_dashes():
    """Test for fix issue #7226."""

    @pydantic.dataclasses.dataclass
    class Foo:
        some_var: str = Field(alias='some-var')

    obj = Foo(**{'some-var': 'some_value'})
    assert obj.some_var == 'some_value'


def test_validate_strings():
    @pydantic.dataclasses.dataclass
    class Nested:
        d: date

    class Model(BaseModel):
        n: Nested

    assert Model.model_validate_strings({'n': {'d': '2017-01-01'}}).n.d == date(2017, 1, 1)


@pytest.mark.parametrize('field_constructor', [dataclasses.field, pydantic.dataclasses.Field])
@pytest.mark.parametrize('extra', ['ignore', 'forbid'])
def test_init_false_not_in_signature(extra, field_constructor):
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra=extra))
    class MyDataclass:
        a: int = field_constructor(init=False, default=-1)
        b: int = pydantic.dataclasses.Field(default=2)

    signature = inspect.signature(MyDataclass)
    # `a` should not be in the __init__
    assert 'a' not in signature.parameters.keys()
    assert 'b' in signature.parameters.keys()


init_test_cases = [
    ({'a': 2, 'b': -1}, 'ignore', {'a': 2, 'b': 1}),
    ({'a': 2}, 'ignore', {'a': 2, 'b': 1}),
    (
        {'a': 2, 'b': -1},
        'forbid',
        [
            {
                'type': 'unexpected_keyword_argument',
                'loc': ('b',),
                'msg': 'Unexpected keyword argument',
                'input': -1,
            }
        ],
    ),
    ({'a': 2}, 'forbid', {'a': 2, 'b': 1}),
]


@pytest.mark.parametrize('field_constructor', [dataclasses.field, pydantic.dataclasses.Field])
@pytest.mark.parametrize(
    'input_data,extra,expected',
    init_test_cases,
)
def test_init_false_with_post_init(input_data, extra, expected, field_constructor):
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra=extra))
    class MyDataclass:
        a: int
        b: int = field_constructor(init=False)

        def __post_init__(self):
            self.b = 1

    if isinstance(expected, list):
        with pytest.raises(ValidationError) as exc_info:
            MyDataclass(**input_data)

        assert exc_info.value.errors(include_url=False) == expected
    else:
        assert dataclasses.asdict(MyDataclass(**input_data)) == expected


@pytest.mark.parametrize('field_constructor', [dataclasses.field, pydantic.dataclasses.Field])
@pytest.mark.parametrize(
    'input_data,extra,expected',
    init_test_cases,
)
def test_init_false_with_default(input_data, extra, expected, field_constructor):
    @pydantic.dataclasses.dataclass(config=ConfigDict(extra=extra))
    class MyDataclass:
        a: int
        b: int = field_constructor(init=False, default=1)

    if isinstance(expected, list):
        with pytest.raises(ValidationError) as exc_info:
            MyDataclass(**input_data)

        assert exc_info.value.errors(include_url=False) == expected
    else:
        assert dataclasses.asdict(MyDataclass(**input_data)) == expected


def test_disallow_extra_allow_and_init_false() -> None:
    with pytest.raises(PydanticUserError, match='This combination is not allowed.'):

        @pydantic.dataclasses.dataclass(config=ConfigDict(extra='allow'))
        class A:
            a: int = Field(init=False, default=1)


def test_disallow_init_false_and_init_var_true() -> None:
    with pytest.raises(PydanticUserError, match='mutually exclusive.'):

        @pydantic.dataclasses.dataclass
        class Foo:
            bar: str = Field(..., init=False, init_var=True)


def test_annotations_valid_for_field_inheritance() -> None:
    # testing https://github.com/pydantic/pydantic/issues/8670

    @pydantic.dataclasses.dataclass()
    class A:
        a: int = pydantic.dataclasses.Field()

    @pydantic.dataclasses.dataclass()
    class B(A): ...

    assert B.__pydantic_fields__['a'].annotation is int

    assert B(a=1).a == 1


def test_annotations_valid_for_field_inheritance_with_existing_field() -> None:
    # variation on testing https://github.com/pydantic/pydantic/issues/8670

    @pydantic.dataclasses.dataclass()
    class A:
        a: int = pydantic.dataclasses.Field()

    @pydantic.dataclasses.dataclass()
    class B(A):
        b: str = pydantic.dataclasses.Field()

    assert B.__pydantic_fields__['a'].annotation is int
    assert B.__pydantic_fields__['b'].annotation is str

    b = B(a=1, b='b')
    assert b.a == 1
    assert b.b == 'b'


def test_annotation_with_double_override() -> None:
    @pydantic.dataclasses.dataclass()
    class A:
        a: int
        b: int
        c: int = pydantic.dataclasses.Field()
        d: int = pydantic.dataclasses.Field()

    # note, the order of fields is different here, as to test that the annotation
    # is correctly set on the field no matter the base's default / current class's default
    @pydantic.dataclasses.dataclass()
    class B(A):
        a: str
        c: str
        b: str = pydantic.dataclasses.Field()
        d: str = pydantic.dataclasses.Field()

    @pydantic.dataclasses.dataclass()
    class C(B): ...

    for class_ in [B, C]:
        instance = class_(a='a', b='b', c='c', d='d')
        for field_name in ['a', 'b', 'c', 'd']:
            assert class_.__pydantic_fields__[field_name].annotation is str
            assert getattr(instance, field_name) == field_name


def test_schema_valid_for_inner_generic() -> None:
    T = TypeVar('T')

    @pydantic.dataclasses.dataclass()
    class Inner(Generic[T]):
        x: T

    @pydantic.dataclasses.dataclass()
    class Outer:
        inner: Inner[int]

    assert Outer(inner={'x': 1}).inner.x == 1
    # note, this isn't Inner[Int] like it is for the BaseModel case, but the type of x is substituted, which is the important part
    assert Outer.__pydantic_core_schema__['schema']['fields'][0]['schema']['cls'] == Inner
    assert (
        Outer.__pydantic_core_schema__['schema']['fields'][0]['schema']['schema']['fields'][0]['schema']['type']
        == 'int'
    )


def test_validation_works_for_cyclical_forward_refs() -> None:
    @pydantic.dataclasses.dataclass()
    class X:
        y: Union['Y', None]

    @pydantic.dataclasses.dataclass()
    class Y:
        x: Union[X, None]

    assert Y(x={'y': None}).x.y is None
