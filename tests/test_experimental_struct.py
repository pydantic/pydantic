import json
import platform
import re
import sys
import warnings
from collections import defaultdict
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from functools import cache, cached_property, partial
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Final,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    get_type_hints,
)
from uuid import UUID, uuid4

import pytest
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    PydanticDeprecatedSince211,
    PydanticUndefinedAnnotation,
    PydanticUserError,
    SecretStr,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    computed_field,
    constr,
    field_validator,
)
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._mock_val_ser import MockCoreSchema
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.experimental.structs import (
    BaseStruct,
    struct_fields,
    to_json,
    to_python,
    validate,
    validate_json,
    validate_strings,
)


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Struct(BaseStruct):
        a: float
        b: int = 10

    m = Struct(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


@pytest.fixture(name='UltraSimpleStruct', scope='session')
def ultra_simple_struct_fixture():
    class UltraSimpleStruct(BaseStruct):
        a: float
        b: int = 10

    return UltraSimpleStruct


def test_ultra_simple_missing(UltraSimpleStruct):
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleStruct()
    assert exc_info.value.errors(include_url=False) == [
        {'loc': ('a',), 'msg': 'Field required', 'type': 'missing', 'input': {}}
    ]
    assert str(exc_info.value) == (
        '1 validation error for UltraSimpleStruct\na\n  Field required [type=missing, input_value={}, input_type=dict]'
    )


def test_ultra_simple_failed(UltraSimpleStruct):
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleStruct(a='x', b='x')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
    ]


def test_ultra_simple_repr(UltraSimpleStruct):
    m = UltraSimpleStruct(a=10.2)
    assert str(m) == 'a=10.2 b=10'
    assert repr(m) == 'UltraSimpleStruct(a=10.2, b=10)'
    assert repr(struct_fields(UltraSimpleStruct)['a']) == 'FieldInfo(annotation=float, required=True)'
    assert repr(struct_fields(UltraSimpleStruct)['b']) == 'FieldInfo(annotation=int, required=False, default=10)'
    assert dict(m) == {'a': 10.2, 'b': 10}
    assert to_python(m) == {'a': 10.2, 'b': 10}
    assert to_json(m) == b'{"a":10.2,"b":10}'
    assert str(m) == 'a=10.2 b=10'


def test_recursive_repr() -> None:
    class A(BaseStruct):
        a: object = None

    class B(BaseStruct):
        a: Optional[A] = None

    a = A()
    a.a = a
    b = B(a=a)

    assert re.match(r"B\(a=A\(a='<Recursion on A with id=\d+>'\)\)", repr(b)) is not None


def test_self_reference_cached_property_repr() -> None:
    class Struct(BaseStruct):
        parent: 'Struct | None' = None
        children: 'list[Struct]' = []

        @computed_field
        @cached_property
        def prop(self) -> bool:
            return True

    foo = Struct()
    bar = Struct()

    foo.children.append(bar)
    bar.parent = foo

    assert (
        str(foo)
        == 'parent=None children=[Struct(parent=Struct(parent=None, children=[...], prop=True), children=[], prop=True)] prop=True'
    )


def test_default_factory_field():
    def myfunc():
        return 1

    class Struct(BaseStruct):
        a: int = Field(default_factory=myfunc)

    m = Struct()
    assert str(m) == 'a=1'
    assert repr(struct_fields(Struct)['a']) == 'FieldInfo(annotation=int, required=False, default_factory=myfunc)'
    assert dict(m) == {'a': 1}
    assert to_json(m) == b'{"a":1}'


def test_comparing(UltraSimpleStruct):
    m = UltraSimpleStruct(a=10.2, b='100')
    assert to_python(m) == {'a': 10.2, 'b': 100}
    assert m != {'a': 10.2, 'b': 100}
    assert m == UltraSimpleStruct(a=10.2, b=100)


@pytest.fixture(scope='session', name='NoneCheckStruct')
def none_check_struct_fix():
    class NoneCheckStruct(BaseStruct):
        existing_str_value: str = 'foo'
        required_str_value: str = ...
        required_str_none_value: Optional[str] = ...
        existing_bytes_value: bytes = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: Optional[bytes] = ...

    return NoneCheckStruct


def test_nullable_strings_success(NoneCheckStruct):
    m = NoneCheckStruct(
        required_str_value='v1', required_str_none_value=None, required_bytes_value='v2', required_bytes_none_value=None
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails(NoneCheckStruct):
    with pytest.raises(ValidationError) as exc_info:
        NoneCheckStruct(
            required_str_value=None,
            required_str_none_value=None,
            required_bytes_value=None,
            required_bytes_none_value=None,
        )
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('required_str_value',),
            'msg': 'Input should be a valid string',
            'input': None,
        },
        {
            'type': 'bytes_type',
            'loc': ('required_bytes_value',),
            'msg': 'Input should be a valid bytes',
            'input': None,
        },
    ]


@pytest.fixture(name='ParentStruct', scope='session')
def parent_sub_struct_fixture():
    class UltraSimpleStruct(BaseStruct):
        a: float
        b: int = 10

    class ParentStruct(BaseStruct):
        grape: bool
        banana: UltraSimpleStruct

    return ParentStruct


def test_parent_sub_struct(ParentStruct):
    m = ParentStruct(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == 'ParentStruct(grape=True, banana=UltraSimpleStruct(a=1.0, b=10))'


def test_parent_sub_struct_fails(ParentStruct):
    with pytest.raises(ValidationError):
        ParentStruct(grape=1, banana=123)


def test_not_required():
    class Struct(BaseStruct):
        a: float = None

    assert Struct(a=12.2).a == 12.2
    assert Struct().a is None
    with pytest.raises(ValidationError) as exc_info:
        Struct(a=None)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_type',
            'loc': ('a',),
            'msg': 'Input should be a valid number',
            'input': None,
        },
    ]


def test_allow_extra():
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        a: float

    m = Struct(a='10.2', b=12)
    assert m.__dict__ == {'a': 10.2}
    assert m.__pydantic_extra__ == {'b': 12}
    assert m.a == 10.2
    assert m.b == 12
    assert m.model_extra == {'b': 12}
    m.c = 42
    assert 'c' not in m.__dict__
    assert m.__pydantic_extra__ == {'b': 12, 'c': 42}
    assert to_python(m) == {'a': 10.2, 'b': 12, 'c': 42}


@pytest.mark.parametrize('extra', ['ignore', 'forbid', 'allow'])
def test_allow_extra_from_attributes(extra: Literal['ignore', 'forbid', 'allow']):
    class Struct(BaseStruct):
        a: float

        model_config = ConfigDict(extra=extra, from_attributes=True)

    class TestClass:
        a = 1.0
        b = 12

    m = validate(Struct, TestClass())
    assert m.a == 1.0
    assert not hasattr(m, 'b')


def test_allow_extra_repr():
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        a: float = ...

    assert str(Struct(a='10.2', b=12)) == 'a=10.2 b=12'


def test_forbidden_extra_success():
    class ForbiddenExtra(BaseStruct):
        model_config = ConfigDict(extra='forbid')
        foo: str = 'whatever'

    m = ForbiddenExtra()
    assert m.foo == 'whatever'


def test_forbidden_extra_fails():
    class ForbiddenExtra(BaseStruct):
        model_config = ConfigDict(extra='forbid')
        foo: str = 'whatever'

    with pytest.raises(ValidationError) as exc_info:
        ForbiddenExtra(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'extra_forbidden',
            'loc': ('bar',),
            'msg': 'Extra inputs are not permitted',
            'input': 'wrong',
        },
        {
            'type': 'extra_forbidden',
            'loc': ('spam',),
            'msg': 'Extra inputs are not permitted',
            'input': 'xx',
        },
    ]


def test_assign_extra_no_validate():
    class Struct(BaseStruct):
        model_config = ConfigDict(validate_assignment=True)
        a: float

    struct = Struct(a=0.2)
    with pytest.raises(ValidationError, match=r"b\s+Object has no attribute 'b'"):
        struct.b = 2


def test_assign_extra_validate():
    class Struct(BaseStruct):
        model_config = ConfigDict(validate_assignment=True)
        a: float

    struct = Struct(a=0.2)
    with pytest.raises(ValidationError, match=r"b\s+Object has no attribute 'b'"):
        struct.b = 2


def test_struct_property_attribute_error():
    class Struct(BaseStruct):
        @property
        def a_property(self):
            raise AttributeError('Internal Error')

    with pytest.raises(AttributeError, match='Internal Error'):
        Struct().a_property


def test_extra_allowed():
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        a: float

    struct = Struct(a=0.2, b=0.1)
    assert struct.b == 0.1

    assert not hasattr(struct, 'c')
    struct.c = 1
    assert hasattr(struct, 'c')
    assert struct.c == 1


def test_reassign_instance_method_with_extra_allow():
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        name: str

        def not_extra_func(self) -> str:
            return f'hello {self.name}'

    def not_extra_func_replacement(self_sub: Struct) -> str:
        return f'hi {self_sub.name}'

    m = Struct(name='james')
    assert m.not_extra_func() == 'hello james'

    m.not_extra_func = partial(not_extra_func_replacement, m)
    assert m.not_extra_func() == 'hi james'
    assert 'not_extra_func' in m.__dict__


def test_extra_ignored():
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='ignore')
        a: float

    struct = Struct(a=0.2, b=0.1)
    assert not hasattr(struct, 'b')

    with pytest.raises(ValueError, match='"Struct" object has no field "b"'):
        struct.b = 1

    assert struct.model_extra is None


def test_field_order_is_preserved_with_extra():
    """This test covers https://github.com/pydantic/pydantic/issues/1234."""

    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')

        a: int
        b: str
        c: float

    struct = Struct(a=1, b='2', c=3.0, d=4)
    assert repr(struct) == "Struct(a=1, b='2', c=3.0, d=4)"
    assert str(to_python(struct)) == "{'a': 1, 'b': '2', 'c': 3.0, 'd': 4}"
    assert str(to_json(struct)) == '{"a":1,"b":"2","c":3.0,"d":4}'


def test_extra_broken_via_pydantic_extra_interference():
    """
    At the time of writing this test there is `_struct_construction.model_extra_getattr` being assigned to struct's
    `__getattr__`. The method then expects `BaseStruct.__pydantic_extra__` isn't `None`. Both this actions happen when
    `model_config.extra` is set to `True`. However, this behavior could be accidentally broken in a subclass of
    `BaseStruct`. In that case `AttributeError` should be thrown when `__getattr__` is being accessed essentially
    disabling the `extra` functionality.
    """

    class BrokenExtraBaseStruct(BaseStruct):
        def model_post_init(self, context: Any, /) -> None:
            super().model_post_init(context)
            object.__setattr__(self, '__pydantic_extra__', None)

    class Struct(BrokenExtraBaseStruct):
        model_config = ConfigDict(extra='allow')

    m = Struct(extra_field='some extra value')

    with pytest.raises(AttributeError) as e:
        m.extra_field

    assert e.value.args == ("'Struct' object has no attribute 'extra_field'",)


def test_model_extra_is_none_when_extra_is_forbid():
    class Foo(BaseStruct):
        model_config = ConfigDict(extra='forbid')

    assert Foo().model_extra is None


def test_set_attr(UltraSimpleStruct):
    m = UltraSimpleStruct(a=10.2)
    assert to_python(m) == {'a': 10.2, 'b': 10}

    m.b = 20
    assert to_python(m) == {'a': 10.2, 'b': 20}


def test_set_attr_invalid():
    class UltraSimpleStruct(BaseStruct):
        a: float = ...
        b: int = 10

    m = UltraSimpleStruct(a=10.2)
    assert to_python(m) == {'a': 10.2, 'b': 10}

    with pytest.raises(ValueError) as exc_info:
        m.c = 20
    assert '"UltraSimpleStruct" object has no field "c"' in exc_info.value.args[0]


def test_any():
    class AnyStruct(BaseStruct):
        a: Any = 10
        b: object = 20

    m = AnyStruct()
    assert m.a == 10
    assert m.b == 20

    m = AnyStruct(a='foobar', b='barfoo')
    assert m.a == 'foobar'
    assert m.b == 'barfoo'


def test_population_by_field_name():
    class Struct(BaseStruct):
        model_config = ConfigDict(validate_by_name=True)
        a: str = Field(alias='_a')

    assert Struct(a='different').a == 'different'
    assert to_python(Struct(a='different')) == {'a': 'different'}
    assert to_python(Struct(a='different'), by_alias=True) == {'_a': 'different'}


def test_field_order():
    class Struct(BaseStruct):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    assert list(struct_fields(Struct).keys()) == ['c', 'b', 'a', 'd']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Struct(BaseStruct):
        a: float
        b: int = 10

    m = Struct(a=10.2)
    assert to_python(m) == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Struct()
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('a',), 'msg': 'Field required', 'input': {}}
    ]


def test_mutability():
    class TestStruct(BaseStruct):
        a: int = 10

        model_config = ConfigDict(extra='forbid', frozen=False)

    m = TestStruct()

    assert m.a == 10
    m.a = 11
    assert m.a == 11


def test_frozen_struct():
    class FrozenStruct(BaseStruct):
        model_config = ConfigDict(extra='forbid', frozen=True)

        a: int = 10

    m = FrozenStruct()
    assert m.a == 10

    with pytest.raises(ValidationError) as exc_info:
        m.a = 11
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': ('a',), 'msg': 'Instance is frozen', 'input': 11}
    ]

    with pytest.raises(ValidationError) as exc_info:
        del m.a
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': ('a',), 'msg': 'Instance is frozen', 'input': None}
    ]

    assert m.a == 10


def test_frozen_struct_cached_property():
    class FrozenStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)

        a: int

        @cached_property
        def test(self) -> int:
            return self.a + 1

    m = FrozenStruct(a=1)

    assert m.test == 2
    # This shouldn't raise:
    del m.test
    m.test = 3
    assert m.test == 3


def test_frozen_field():
    class FrozenStruct(BaseStruct):
        a: int = Field(10, frozen=True)

    m = FrozenStruct()
    assert m.a == 10

    with pytest.raises(ValidationError) as exc_info:
        m.a = 11
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_field', 'loc': ('a',), 'msg': 'Field is frozen', 'input': 11}
    ]

    with pytest.raises(ValidationError) as exc_info:
        del m.a
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_field', 'loc': ('a',), 'msg': 'Field is frozen', 'input': None}
    ]

    assert m.a == 10


def test_not_frozen_are_not_hashable():
    class TestStruct(BaseStruct):
        a: int = 10

    m = TestStruct()
    with pytest.raises(TypeError) as exc_info:
        hash(m)
    assert "unhashable type: 'TestStruct'" in exc_info.value.args[0]


def test_with_declared_hash():
    class Foo(BaseStruct):
        x: int

        def __hash__(self):
            return self.x**2

    class Bar(Foo):
        y: int

        def __hash__(self):
            return self.y**3

    class Buz(Bar):
        z: int

    assert hash(Foo(x=2)) == 4
    assert hash(Bar(x=2, y=3)) == 27
    assert hash(Buz(x=2, y=3, z=4)) == 27


def test_frozen_with_hashable_fields_are_hashable():
    class TestStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)
        a: int = 10

    m = TestStruct()
    assert m.__hash__ is not None
    assert isinstance(hash(m), int)


def test_frozen_with_unhashable_fields_are_not_hashable():
    class TestStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)
        a: int = 10
        y: list[int] = [1, 2, 3]

    m = TestStruct()
    with pytest.raises(TypeError) as exc_info:
        hash(m)
    assert "unhashable type: 'list'" in exc_info.value.args[0]


def test_hash_function_empty_struct():
    class TestStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)

    m = TestStruct()
    m2 = TestStruct()
    assert m == m2
    assert hash(m) == hash(m2)


def test_hash_function_give_different_result_for_different_object():
    class TestStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)

        a: int = 10

    m = TestStruct()
    m2 = TestStruct()
    m3 = TestStruct(a=11)
    assert hash(m) == hash(m2)
    assert hash(m) != hash(m3)


def test_hash_function_works_when_instance_dict_modified():
    class TestStruct(BaseStruct):
        model_config = ConfigDict(frozen=True)

        a: int
        b: int

    m = TestStruct(a=1, b=2)
    h = hash(m)

    # Test edge cases where __dict__ is modified
    # @functools.cached_property can add keys to __dict__, these should be ignored.
    m.__dict__['c'] = 1
    assert hash(m) == h

    # Order of keys can be changed, e.g. with the deprecated copy method, which shouldn't matter.
    m.__dict__ = {'b': 2, 'a': 1}
    assert hash(m) == h

    # Keys can be missing, e.g. when using the deprecated copy method.
    # This could change the hash, and more importantly hashing shouldn't raise a KeyError
    # We don't assert here, because a hash collision is possible: the hash is not guaranteed to change
    # However, hashing must not raise an exception, which simply calling hash() checks for
    del m.__dict__['a']
    hash(m)


def test_default_hash_function_overrides_default_hash_function():
    class A(BaseStruct):
        model_config = ConfigDict(frozen=True)

        x: int

    class B(A):
        model_config = ConfigDict(frozen=True)

        y: int

    assert A.__hash__ != B.__hash__
    assert hash(A(x=1)) != hash(B(x=1, y=2)) != hash(B(x=1, y=3))


def test_hash_method_is_inherited_for_frozen_structs():
    class MyBaseStruct(BaseStruct):
        """A base struct with sensible configurations."""

        model_config = ConfigDict(frozen=True)

        def __hash__(self):
            return hash(id(self))

    class MySubClass(MyBaseStruct):
        x: dict[str, int]

        @cache
        def cached_method(self):
            return len(self.x)

    my_instance = MySubClass(x={'a': 1, 'b': 2})
    assert my_instance.cached_method() == 2

    object.__setattr__(my_instance, 'x', {})  # can't change the "normal" way due to frozen
    assert my_instance.cached_method() == 2


@pytest.fixture(name='ValidateAssignmentStruct', scope='session')
def validate_assignment_fixture():
    class ValidateAssignmentStruct(BaseStruct):
        model_config = ConfigDict(validate_assignment=True)
        a: int = 2
        b: constr(min_length=1)

    return ValidateAssignmentStruct


def test_validating_assignment_pass(ValidateAssignmentStruct):
    p = ValidateAssignmentStruct(a=5, b='hello')
    p.a = 2
    assert p.a == 2
    assert to_python(p) == {'a': 2, 'b': 'hello'}
    p.b = 'hi'
    assert p.b == 'hi'
    assert to_python(p) == {'a': 2, 'b': 'hi'}


@pytest.mark.parametrize('init_valid', [False, True])
def test_validating_assignment_fail(ValidateAssignmentStruct, init_valid: bool):
    p = ValidateAssignmentStruct(a=5, b='hello')
    if init_valid:
        p.a = 5
        p.b = 'hello'

    with pytest.raises(ValidationError) as exc_info:
        p.a = 'b'
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        p.b = ''
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_short',
            'loc': ('b',),
            'msg': 'String should have at least 1 character',
            'input': '',
            'ctx': {'min_length': 1},
        }
    ]


class Foo(Enum):
    FOO = 'foo'
    BAR = 'bar'


@pytest.mark.parametrize('value', [Foo.FOO, Foo.FOO.value, 'foo'])
def test_enum_values(value: Any) -> None:
    class Struct(BaseStruct):
        foo: Foo
        model_config = ConfigDict(use_enum_values=True)

    m = Struct(foo=value)

    foo = m.foo
    assert type(foo) is str, type(foo)
    assert foo == 'foo'

    foo = to_python(m)['foo']
    assert type(foo) is str, type(foo)
    assert foo == 'foo'


def test_literal_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo_value', 'bar': 'bar_value'})

    class Struct(BaseStruct):
        baz: Literal[FooEnum.foo]
        boo: str = 'hoo'
        model_config = ConfigDict(use_enum_values=True)

    m = Struct(baz=FooEnum.foo)
    assert to_python(m) == {'baz': 'foo_value', 'boo': 'hoo'}
    assert to_python(m, mode='json') == {'baz': 'foo_value', 'boo': 'hoo'}
    assert m.baz == 'foo_value'

    with pytest.raises(ValidationError) as exc_info:
        Struct(baz=FooEnum.bar)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('baz',),
            'msg': "Input should be <FooEnum.foo: 'foo_value'>",
            'input': FooEnum.bar,
            'ctx': {'expected': "<FooEnum.foo: 'foo_value'>"},
        }
    ]


class StrFoo(str, Enum):
    FOO = 'foo'
    BAR = 'bar'


@pytest.mark.parametrize('value', [StrFoo.FOO, StrFoo.FOO.value, 'foo', 'hello'])
def test_literal_use_enum_values_multi_type(value) -> None:
    class Struct(BaseStruct):
        baz: Literal[StrFoo.FOO, 'hello']
        model_config = ConfigDict(use_enum_values=True)

    assert isinstance(Struct(baz=value).baz, str)


def test_literal_use_enum_values_with_default() -> None:
    class Struct(BaseStruct):
        baz: Literal[StrFoo.FOO] = Field(default=StrFoo.FOO)
        model_config = ConfigDict(use_enum_values=True, validate_default=True)

    validated = Struct()
    assert type(validated.baz) is str
    assert type(to_python(validated)['baz']) is str

    validated = validate_json(Struct, '{"baz": "foo"}')
    assert type(validated.baz) is str
    assert type(to_python(validated)['baz']) is str

    validated = validate(Struct, {'baz': StrFoo.FOO})
    assert type(validated.baz) is str
    assert type(to_python(validated)['baz']) is str


def test_strict_enum_values():
    class MyEnum(Enum):
        val = 'val'

    class Struct(BaseStruct):
        model_config = ConfigDict(use_enum_values=True)
        x: MyEnum

    assert validate(Struct, {'x': MyEnum.val}, strict=True).x == 'val'


def test_union_enum_values():
    class MyEnum(Enum):
        val = 'val'

    class NormalStruct(BaseStruct):
        x: Union[MyEnum, int]

    class UseEnumValuesStruct(BaseStruct):
        model_config = ConfigDict(use_enum_values=True)
        x: Union[MyEnum, int]

    assert NormalStruct(x=MyEnum.val).x != 'val'
    assert UseEnumValuesStruct(x=MyEnum.val).x == 'val'


def test_enum_raw():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Struct(BaseStruct):
        foo: FooEnum = None

    m = Struct(foo='foo')
    assert isinstance(m.foo, FooEnum)
    assert m.foo != 'foo'
    assert m.foo.value == 'foo'


def test_set_tuple_values():
    class Struct(BaseStruct):
        foo: set
        bar: tuple

    m = Struct(foo=['a', 'b'], bar=['c', 'd'])
    assert m.foo == {'a', 'b'}
    assert m.bar == ('c', 'd')
    assert to_python(m) == {'foo': {'a', 'b'}, 'bar': ('c', 'd')}


def test_default_copy():
    class User(BaseStruct):
        friends: list[int] = Field(default_factory=list)

    u1 = User()
    u2 = User()
    assert u1.friends is not u2.friends


class ArbitraryType:
    pass


def test_arbitrary_type_allowed_validation_success():
    class ArbitraryTypeAllowedStruct(BaseStruct):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        t: ArbitraryType

    arbitrary_type_instance = ArbitraryType()
    m = ArbitraryTypeAllowedStruct(t=arbitrary_type_instance)
    assert m.t == arbitrary_type_instance


class OtherClass:
    pass


def test_arbitrary_type_allowed_validation_fails():
    class ArbitraryTypeAllowedStruct(BaseStruct):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        t: ArbitraryType

    input_value = OtherClass()
    with pytest.raises(ValidationError) as exc_info:
        ArbitraryTypeAllowedStruct(t=input_value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('t',),
            'msg': 'Input should be an instance of ArbitraryType',
            'input': input_value,
            'ctx': {'class': 'ArbitraryType'},
        }
    ]


def test_arbitrary_types_not_allowed():
    with pytest.raises(TypeError, match='Unable to generate pydantic-core schema for <class'):

        class ArbitraryTypeNotAllowedStruct(BaseStruct):
            t: ArbitraryType


@pytest.fixture(scope='session', name='TypeTypeStruct')
def type_type_struct_fixture():
    class TypeTypeStruct(BaseStruct):
        t: type[ArbitraryType]

    return TypeTypeStruct


def test_type_type_validation_success(TypeTypeStruct):
    arbitrary_type_class = ArbitraryType
    m = TypeTypeStruct(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_subclass_validation_success(TypeTypeStruct):
    class ArbitrarySubType(ArbitraryType):
        pass

    arbitrary_type_class = ArbitrarySubType
    m = TypeTypeStruct(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


@pytest.mark.parametrize('input_value', [OtherClass, 1])
def test_type_type_validation_fails(TypeTypeStruct, input_value):
    with pytest.raises(ValidationError) as exc_info:
        TypeTypeStruct(t=input_value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_subclass_of',
            'loc': ('t',),
            'msg': 'Input should be a subclass of ArbitraryType',
            'input': input_value,
            'ctx': {'class': 'ArbitraryType'},
        }
    ]


@pytest.mark.parametrize('bare_type', [type, type])
def test_bare_type_type_validation_success(bare_type):
    class TypeTypeStruct(BaseStruct):
        t: bare_type

    arbitrary_type_class = ArbitraryType
    m = TypeTypeStruct(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


@pytest.mark.parametrize('bare_type', [type, type])
def test_bare_type_type_validation_fails(bare_type):
    class TypeTypeStruct(BaseStruct):
        t: bare_type

    arbitrary_type = ArbitraryType()
    with pytest.raises(ValidationError) as exc_info:
        TypeTypeStruct(t=arbitrary_type)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_type',
            'loc': ('t',),
            'msg': 'Input should be a type',
            'input': arbitrary_type,
        }
    ]


def test_value_field_name_shadows_attribute():
    with pytest.raises(PydanticUserError, match="A non-annotated attribute was detected: `model_json_schema = 'abc'`"):

        class BadStruct(BaseStruct):
            model_json_schema = (
                'abc'  # This conflicts with the BaseStruct's model_json_schema() class method, but has no annotation
            )


def test_class_var():
    class MyStruct(BaseStruct):
        a: ClassVar
        b: ClassVar[int] = 1
        c: int = 2

    assert list(struct_fields(MyStruct).keys()) == ['c']

    class MyOtherStruct(MyStruct):
        a = ''
        b = 2

    assert list(struct_fields(MyOtherStruct).keys()) == ['c']


def test_fields_set():
    class MyStruct(BaseStruct):
        a: int
        b: int = 2

    m = MyStruct(a=5)
    assert m.model_fields_set == {'a'}

    m.b = 2
    assert m.model_fields_set == {'a', 'b'}

    m = MyStruct(a=5, b=2)
    assert m.model_fields_set == {'a', 'b'}


def test_exclude_unset_dict():
    class MyStruct(BaseStruct):
        a: int
        b: int = 2

    m = MyStruct(a=5)
    assert to_python(m, exclude_unset=True) == {'a': 5}

    m = MyStruct(a=5, b=3)
    assert to_python(m, exclude_unset=True) == {'a': 5, 'b': 3}


def test_exclude_unset_recursive():
    class StructA(BaseStruct):
        a: int
        b: int = 1

    class StructB(BaseStruct):
        c: int
        d: int = 2
        e: StructA

    m = StructB(c=5, e={'a': 0})
    assert to_python(m) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert to_python(m, exclude_unset=True) == {'c': 5, 'e': {'a': 0}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': StructA(a=0, b=1)}


def test_dict_exclude_unset_populated_by_alias():
    class MyStruct(BaseStruct):
        model_config = ConfigDict(validate_by_name=True)
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

    m = MyStruct(alias_a='a')

    assert to_python(m, exclude_unset=True) == {'a': 'a'}
    assert to_python(m, exclude_unset=True, by_alias=True) == {'alias_a': 'a'}


def test_dict_exclude_unset_populated_by_alias_with_extra():
    class MyStruct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

    m = MyStruct(alias_a='a', c='c')

    assert to_python(m, exclude_unset=True) == {'a': 'a', 'c': 'c'}
    assert to_python(m, exclude_unset=True, by_alias=True) == {'alias_a': 'a', 'c': 'c'}


def test_exclude_defaults():
    class Struct(BaseStruct):
        mandatory: str
        nullable_mandatory: Optional[str] = ...
        facultative: str = 'x'
        nullable_facultative: Optional[str] = None

    m = Struct(mandatory='a', nullable_mandatory=None)
    assert to_python(m, exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
    }

    m = Struct(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative=None)
    assert to_python(m, exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
        'facultative': 'y',
    }

    m = Struct(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative='z')
    assert to_python(m, exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
        'facultative': 'y',
        'nullable_facultative': 'z',
    }


def test_dir_fields():
    class MyStruct(BaseStruct):
        attribute_a: int
        attribute_b: int = 2

    m = MyStruct(attribute_a=5)

    # structs do not have model methods
    assert 'model_dump' not in dir(m)
    assert 'model_dump_json' not in dir(m)

    # ... but they do have `dir`
    assert 'attribute_a' in dir(m)
    assert 'attribute_b' in dir(m)


def test_dict_with_extra_keys():
    class MyStruct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        a: str = Field(None, alias='alias_a')

    m = MyStruct(extra_key='extra')
    assert to_python(m) == {'a': None, 'extra_key': 'extra'}
    assert to_python(m, by_alias=True) == {'alias_a': None, 'extra_key': 'extra'}


def test_ignored_types():
    from pydantic.experimental.structs import BaseStruct

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    class Struct(BaseStruct):
        model_config = ConfigDict(ignored_types=(classproperty,))

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    assert Struct.class_name == 'Struct'
    assert Struct().class_name == 'Struct'


def test_struct_iteration():
    class Foo(BaseStruct):
        a: int = 1
        b: int = 2

    class Bar(BaseStruct):
        c: int
        d: Foo

    m = Bar(c=3, d={})
    assert to_python(m) == {'c': 3, 'd': {'a': 1, 'b': 2}}
    assert list(m) == [('c', 3), ('d', Foo())]
    assert dict(m) == {'c': 3, 'd': Foo()}


def test_struct_iteration_extra() -> None:
    class Foo(BaseStruct):
        x: int = 1

    class Bar(BaseStruct):
        a: int
        b: Foo
        model_config = ConfigDict(extra='allow')

    m = validate(Bar, {'a': 1, 'b': {}, 'c': 2, 'd': Foo()})
    assert to_python(m) == {'a': 1, 'b': {'x': 1}, 'c': 2, 'd': {'x': 1}}
    assert list(m) == [('a', 1), ('b', Foo()), ('c', 2), ('d', Foo())]
    assert dict(m) == {'a': 1, 'b': Foo(), 'c': 2, 'd': Foo()}


@pytest.mark.parametrize(
    'exclude,expected,raises_match',
    [
        pytest.param(
            None,
            {'c': 3, 'foos': [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]},
            None,
            id='exclude nothing',
        ),
        pytest.param(
            {'foos': {0: {'a'}, 1: {'a'}}},
            {'c': 3, 'foos': [{'b': 2}, {'b': 4}]},
            None,
            id='excluding fields of indexed list items',
        ),
        pytest.param(
            {'foos': {'a'}},
            {'c': 3, 'foos': [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]},
            None,
            id='Trying to exclude string keys on list field should be ignored (1)',
        ),
        pytest.param(
            {'foos': {0: ..., 'a': ...}},
            {'c': 3, 'foos': [{'a': 3, 'b': 4}]},
            None,
            id='Trying to exclude string keys on list field should be ignored (2)',
        ),
        pytest.param(
            {'foos': {0: 1}},
            TypeError,
            '`exclude` argument must be a set or dict',
            id='value as int should be an error',
        ),
        pytest.param(
            {'foos': {'__all__': {1}}},
            {'c': 3, 'foos': [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]},
            None,
            id='excluding int in dict should have no effect',
        ),
        pytest.param(
            {'foos': {'__all__': {'a'}}},
            {'c': 3, 'foos': [{'b': 2}, {'b': 4}]},
            None,
            id='using "__all__" to exclude specific nested field',
        ),
        pytest.param(
            {'foos': {0: {'b'}, '__all__': {'a'}}},
            {'c': 3, 'foos': [{}, {'b': 4}]},
            None,
            id='using "__all__" to exclude specific nested field in combination with more specific exclude',
        ),
        pytest.param(
            {'foos': {'__all__'}},
            {'c': 3, 'foos': []},
            None,
            id='using "__all__" to exclude all list items',
        ),
        pytest.param(
            {'foos': {1, '__all__'}},
            {'c': 3, 'foos': []},
            None,
            id='using "__all__" and other items should get merged together, still excluding all list items',
        ),
        pytest.param(
            {'foos': {-1: {'b'}}},
            {'c': 3, 'foos': [{'a': 1, 'b': 2}, {'a': 3}]},
            None,
            id='negative indexes',
        ),
    ],
)
def test_struct_export_nested_list(exclude, expected, raises_match):
    class Foo(BaseStruct):
        a: int = 1
        b: int = 2

    class Bar(BaseStruct):
        c: int
        foos: list[Foo]

    m = Bar(c=3, foos=[Foo(a=1, b=2), Foo(a=3, b=4)])

    if raises_match is not None:
        with pytest.raises(expected, match=raises_match):
            to_python(m, exclude=exclude)
    else:
        original_exclude = deepcopy(exclude)
        assert to_python(m, exclude=exclude) == expected
        assert exclude == original_exclude


@pytest.mark.parametrize(
    'excludes,expected',
    [
        pytest.param(
            {'bars': {0}},
            {'a': 1, 'bars': [{'y': 2}, {'w': -1, 'z': 3}]},
            id='excluding first item from list field using index',
        ),
        pytest.param({'bars': {'__all__'}}, {'a': 1, 'bars': []}, id='using "__all__" to exclude all list items'),
        pytest.param(
            {'bars': {'__all__': {'w'}}},
            {'a': 1, 'bars': [{'x': 1}, {'y': 2}, {'z': 3}]},
            id='exclude single dict key from all list items',
        ),
    ],
)
def test_struct_export_dict_exclusion(excludes, expected):
    class Foo(BaseStruct):
        a: int = 1
        bars: list[dict[str, int]]

    m = Foo(a=1, bars=[{'w': 0, 'x': 1}, {'y': 2}, {'w': -1, 'z': 3}])

    original_excludes = deepcopy(excludes)
    assert to_python(m, exclude=excludes) == expected
    assert excludes == original_excludes


def test_field_exclude():
    class User(BaseStruct):
        _priv: int = PrivateAttr()
        id: int
        username: str
        password: SecretStr = Field(exclude=True)
        hobbies: list[str]

    my_user = User(id=42, username='JohnDoe', password='hashedpassword', hobbies=['scuba diving'])

    my_user._priv = 13
    assert my_user.id == 42
    assert my_user.password.get_secret_value() == 'hashedpassword'
    assert to_python(my_user) == {'id': 42, 'username': 'JohnDoe', 'hobbies': ['scuba diving']}


def test_field_exclude_if() -> None:
    class Struct(BaseStruct):
        a: int = Field(exclude_if=lambda x: x > 1)
        b: str = Field(exclude_if=lambda x: 'foo' in x)

    assert to_python(Struct(a=0, b='bar')) == {'a': 0, 'b': 'bar'}
    assert to_python(Struct(a=2, b='bar')) == {'b': 'bar'}
    assert to_python(Struct(a=0, b='foo')) == {'a': 0}
    assert to_python(Struct(a=0, b='foo'), exclude={'a'}) == {}
    assert to_python(Struct(a=2, b='foo')) == {}

    assert to_json(Struct(a=0, b='bar')) == '{"a":0,"b":"bar"}'
    assert to_json(Struct(a=2, b='bar')) == '{"b":"bar"}'
    assert to_json(Struct(a=0, b='foo')) == '{"a":0}'
    assert to_json(Struct(a=0, b='foo'), exclude={'a'}) == '{}'
    assert to_json(Struct(a=2, b='foo')) == '{}'


def test_revalidate_instances_never():
    class User(BaseStruct):
        hobbies: list[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseStruct):
        user: User

    t = Transaction(user=my_user)

    assert t.user is my_user
    assert t.user.hobbies is my_user.hobbies

    class SubUser(User):
        sins: list[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is my_sub_user
    assert t.user.hobbies is my_sub_user.hobbies


def test_revalidate_instances_sub_instances():
    class User(BaseStruct, revalidate_instances='subclass-instances'):
        hobbies: list[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseStruct):
        user: User

    t = Transaction(user=my_user)

    assert t.user is my_user
    assert t.user.hobbies is my_user.hobbies

    class SubUser(User):
        sins: list[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is not my_sub_user
    assert t.user.hobbies is not my_sub_user.hobbies
    assert not hasattr(t.user, 'sins')


def test_revalidate_instances_always():
    class User(BaseStruct, revalidate_instances='always'):
        hobbies: list[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseStruct):
        user: User

    t = Transaction(user=my_user)

    assert t.user is not my_user
    assert t.user.hobbies is not my_user.hobbies

    class SubUser(User):
        sins: list[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is not my_sub_user
    assert t.user.hobbies is not my_sub_user.hobbies
    assert not hasattr(t.user, 'sins')


def test_revalidate_instances_always_list_of_struct_instance():
    class A(BaseStruct):
        model_config = ConfigDict(revalidate_instances='always')
        name: str

    class B(BaseStruct):
        list_a: list[A]

    a = A(name='a')
    b = B(list_a=[a])
    assert b.list_a == [A(name='a')]
    a.name = 'b'
    assert b.list_a == [A(name='a')]


@pytest.mark.skip(reason='not implemented')
@pytest.mark.parametrize(
    'kinds',
    [
        {'sub_fields', 'model_fields', 'model_config', 'sub_config', 'combined_config'},
        {'sub_fields', 'model_fields', 'combined_config'},
        {'sub_fields', 'model_fields'},
        {'combined_config'},
        {'model_config', 'sub_config'},
        {'model_config', 'sub_fields'},
        {'model_fields', 'sub_config'},
    ],
)
@pytest.mark.parametrize(
    'exclude,expected',
    [
        (None, {'a': 0, 'c': {'a': [3, 5], 'c': 'foobar'}, 'd': {'c': 'foobar'}}),
        ({'c', 'd'}, {'a': 0}),
        ({'a': ..., 'c': ..., 'd': {'a': ..., 'c': ...}}, {'d': {}}),
    ],
)
def test_struct_export_exclusion_with_fields_and_config(kinds, exclude, expected):
    """Test that exporting structs with fields using the export parameter works."""

    class ChildConfig:
        pass

    if 'sub_config' in kinds:
        ChildConfig.fields = {'b': {'exclude': ...}, 'a': {'exclude': {1}}}

    class ParentConfig:
        pass

    if 'combined_config' in kinds:
        ParentConfig.fields = {
            'b': {'exclude': ...},
            'c': {'exclude': {'b': ..., 'a': {1}}},
            'd': {'exclude': {'a': ..., 'b': ...}},
        }

    elif 'model_config' in kinds:
        ParentConfig.fields = {'b': {'exclude': ...}, 'd': {'exclude': {'a'}}}

    class Sub(BaseStruct):
        a: list[int] = Field([3, 4, 5], exclude={1} if 'sub_fields' in kinds else None)
        b: int = Field(4, exclude=... if 'sub_fields' in kinds else None)
        c: str = 'foobar'

        Config = ChildConfig

    class Struct(BaseStruct):
        a: int = 0
        b: int = Field(2, exclude=... if 'model_fields' in kinds else None)
        c: Sub = Sub()
        d: Sub = Field(Sub(), exclude={'a'} if 'model_fields' in kinds else None)

        Config = ParentConfig

    m = Struct()
    assert to_python(m, exclude=exclude) == expected, 'Unexpected struct export result'


@pytest.mark.skip(reason='not implemented')
def test_struct_export_exclusion_inheritance():
    class Sub(BaseStruct):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = Field('v4', exclude=...)

    class Parent(BaseStruct):
        model_config = ConfigDict(fields={'a': {'exclude': ...}, 's': {'exclude': {'s1'}}})
        a: int
        b: int = Field(exclude=...)
        c: int
        d: int
        s: Sub = Sub()

    class Child(Parent):
        model_config = ConfigDict(fields={'c': {'exclude': ...}, 's': {'exclude': {'s2'}}})

    actual = to_python(Child(a=0, b=1, c=2, d=3))
    expected = {'d': 3, 's': {'s3': 'v3'}}
    assert actual == expected, 'Unexpected struct export result'


@pytest.mark.skip(reason='not implemented')
def test_struct_export_with_true_instead_of_ellipsis():
    class Sub(BaseStruct):
        s1: int = 1

    class Struct(BaseStruct):
        model_config = ConfigDict(fields={'c': {'exclude': True}})
        a: int = 2
        b: int = Field(3, exclude=True)
        c: int = Field(4)
        s: Sub = Sub()

    m = Struct()
    assert to_python(m, exclude={'s': True}) == {'a': 2}


@pytest.mark.skip(reason='not implemented')
def test_struct_export_inclusion():
    class Sub(BaseStruct):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = 'v4'

    class Struct(BaseStruct):
        model_config = ConfigDict(
            fields={'a': {'include': {'s2', 's1', 's3'}}, 'b': {'include': {'s1', 's2', 's3', 's4'}}}
        )
        a: Sub = Sub()
        b: Sub = Field(Sub(), include={'s1'})
        c: Sub = Field(Sub(), include={'s1', 's2'})

    assert struct_fields(Struct)['a'].field_info.include == {'s1': ..., 's2': ..., 's3': ...}
    assert struct_fields(Struct)['b'].field_info.include == {'s1': ...}
    assert struct_fields(Struct)['c'].field_info.include == {'s1': ..., 's2': ...}

    actual = to_python(Struct(), include={'a': {'s3', 's4'}, 'b': ..., 'c': ...})
    # s1 included via field, s2 via config and s3 via .dict call:
    expected = {'a': {'s3': 'v3'}, 'b': {'s1': 'v1'}, 'c': {'s1': 'v1', 's2': 'v2'}}

    assert actual == expected, 'Unexpected struct export result'


@pytest.mark.skip(reason='not implemented')
def test_struct_export_inclusion_inheritance():
    class Sub(BaseStruct):
        s1: str = Field('v1', include=...)
        s2: str = Field('v2', include=...)
        s3: str = Field('v3', include=...)
        s4: str = 'v4'

    class Parent(BaseStruct):
        # b will be included since fields are set independently
        model_config = ConfigDict(fields={'b': {'include': ...}})
        a: int
        b: int
        c: int
        s: Sub = Field(Sub(), include={'s1', 's2'})  # overrides includes set in Sub struct

    class Child(Parent):
        # b is still included even if it doesn't occur here since fields
        # are still considered separately.
        # s however, is merged, resulting in only s1 being included.
        model_config = ConfigDict(fields={'a': {'include': ...}, 's': {'include': {'s1'}}})

    actual = to_python(Child(a=0, b=1, c=2))
    expected = {'a': 0, 'b': 1, 's': {'s1': 'v1'}}
    assert actual == expected, 'Unexpected struct export result'


def test_untyped_fields_warning():
    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            'A non-annotated attribute was detected: `x = 1`. All struct fields require a type annotation; '
            'if `x` is not meant to be a field, you may be able to resolve this error by annotating it '
            "as a `ClassVar` or updating `model_config['ignored_types']`."
        ),
    ):

        class WarningStruct(BaseStruct):
            x = 1

    # Prove that annotating with ClassVar prevents the warning
    class NonWarningStruct(BaseStruct):
        x: ClassVar = 1


def test_untyped_fields_error():
    with pytest.raises(TypeError, match="Field 'a' requires a type annotation"):

        class Struct(BaseStruct):
            a = Field('foobar')


def test_custom_init_subclass_params():
    class DerivedStruct(BaseStruct):
        def __init_subclass__(cls, something):
            cls.something = something

    # if this raises a TypeError, then there is a regression of issue 867:
    # pydantic.main.MetaStruct.__new__ should include **kwargs at the end of the
    # method definition and pass them on to the super call at the end in order
    # to allow the special method __init_subclass__ to be defined with custom
    # parameters on extended BaseStruct classes.
    class NewStruct(DerivedStruct, something=2):
        something: ClassVar = 1

    assert NewStruct.something == 2


def test_recursive_struct():
    class MyStruct(BaseStruct):
        field: Optional['MyStruct']

    m = MyStruct(field={'field': {'field': None}})
    assert to_python(m) == {'field': {'field': {'field': None}}}


def test_recursive_cycle_with_repeated_field():
    class A(BaseStruct):
        b: 'B'

    class B(BaseStruct):
        a1: Optional[A] = None
        a2: Optional[A] = None

    A.model_rebuild()

    assert validate(A, {'b': {'a1': {'b': {'a1': None}}}}) == A(b=B(a1=A(b=B(a1=None))))
    with pytest.raises(ValidationError) as exc_info:
        validate(A, {'b': {'a1': {'a1': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'a1': None}, 'loc': ('b', 'a1', 'b'), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_two_defaults():
    with pytest.raises(TypeError, match='^cannot specify both default and default_factory$'):

        class Struct(BaseStruct):
            a: int = Field(default=3, default_factory=lambda: 3)


def test_default_factory():
    class ValueStruct(BaseStruct):
        uid: UUID = uuid4()

    m1 = ValueStruct()
    m2 = ValueStruct()
    assert m1.uid == m2.uid

    class DynamicValueStruct(BaseStruct):
        uid: UUID = Field(default_factory=uuid4)

    m1 = DynamicValueStruct()
    m2 = DynamicValueStruct()
    assert isinstance(m1.uid, UUID)
    assert m1.uid != m2.uid

    # With a callable: we still should be able to set callables as defaults
    class FunctionStruct(BaseStruct):
        a: int = 1
        uid: Callable[[], UUID] = Field(uuid4)

    m = FunctionStruct()
    assert m.uid is uuid4

    # Returning a singleton from a default_factory is supported
    class MySingleton:
        pass

    MY_SINGLETON = MySingleton()

    class SingletonFieldStruct(BaseStruct):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        singleton: MySingleton = Field(default_factory=lambda: MY_SINGLETON)

    assert SingletonFieldStruct().singleton is SingletonFieldStruct().singleton


def test_default_factory_called_once():
    """It should call only once the given factory by default"""

    class Seq:
        def __init__(self):
            self.v = 0

        def __call__(self):
            self.v += 1
            return self.v

    class MyStruct(BaseStruct):
        id: int = Field(default_factory=Seq())

    m1 = MyStruct()
    assert m1.id == 1
    m2 = MyStruct()
    assert m2.id == 2
    assert m1.id == 1


def test_default_factory_called_once_2():
    """It should call only once the given factory by default"""

    v = 0

    def factory():
        nonlocal v
        v += 1
        return v

    class MyStruct(BaseStruct):
        id: int = Field(default_factory=factory)

    m1 = MyStruct()
    assert m1.id == 1
    m2 = MyStruct()
    assert m2.id == 2


def test_default_factory_validate_children():
    class Child(BaseStruct):
        x: int

    class Parent(BaseStruct):
        children: list[Child] = Field(default_factory=list)

    Parent(children=[{'x': 1}, {'x': 2}])
    with pytest.raises(ValidationError) as exc_info:
        Parent(children=[{'x': 1}, {'y': 2}])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('children', 1, 'x'), 'msg': 'Field required', 'input': {'y': 2}}
    ]


def test_default_factory_parse():
    class Inner(BaseStruct):
        val: int = Field(0)

    class Outer(BaseStruct):
        inner_1: Inner = Field(default_factory=Inner)
        inner_2: Inner = Field(Inner())

    default = to_python(Outer())
    parsed = validate(Outer, default)
    assert to_python(parsed) == {'inner_1': {'val': 0}, 'inner_2': {'val': 0}}
    assert repr(parsed) == 'Outer(inner_1=Inner(val=0), inner_2=Inner(val=0))'


def test_default_factory_validated_data_arg() -> None:
    class Struct(BaseStruct):
        a: int = 1
        b: int = Field(default_factory=lambda data: data['a'])

    struct = Struct()
    assert struct.b == 1

    struct = Struct.struct_construct(a=1)
    assert struct.b == 1

    class InvalidStruct(BaseStruct):
        a: int = Field(default_factory=lambda data: data['b'])
        b: int

    with pytest.raises(KeyError):
        InvalidStruct(b=2)


def test_default_factory_validated_data_arg_not_required() -> None:
    def fac(data: Optional[dict[str, Any]] = None):
        if data is not None:
            return data['a']
        return 3

    class Struct(BaseStruct):
        a: int = 1
        b: int = Field(default_factory=fac)

    struct = Struct()
    assert struct.b == 3


def test_reuse_same_field():
    required_field = Field()

    class Struct1(BaseStruct):
        required: str = required_field

    class Struct2(BaseStruct):
        required: str = required_field

    with pytest.raises(ValidationError):
        validate(Struct1, {})
    with pytest.raises(ValidationError):
        validate(Struct2, {})


def test_base_config_type_hinting():
    class M(BaseStruct):
        a: int

    get_type_hints(type(M.model_config))


def test_frozen_field_with_validate_assignment():
    """assigning a frozen=True field should raise a TypeError"""

    class Entry(BaseStruct):
        model_config = ConfigDict(validate_assignment=True)
        id: float = Field(frozen=True)
        val: float

    r = Entry(id=1, val=100)
    assert r.val == 100
    r.val = 101
    assert r.val == 101
    assert r.id == 1
    with pytest.raises(ValidationError) as exc_info:
        r.id = 2
    assert exc_info.value.errors(include_url=False) == [
        {'input': 2, 'loc': ('id',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]


def test_repr_field():
    class Struct(BaseStruct):
        a: int = Field()
        b: float = Field(repr=True)
        c: bool = Field(repr=False)

    m = Struct(a=1, b=2.5, c=True)
    assert repr(m) == 'Struct(a=1, b=2.5)'
    assert repr(struct_fields(Struct)['a']) == 'FieldInfo(annotation=int, required=True)'
    assert repr(struct_fields(Struct)['b']) == 'FieldInfo(annotation=float, required=True)'
    assert repr(struct_fields(Struct)['c']) == 'FieldInfo(annotation=bool, required=True, repr=False)'


def test_inherited_struct_field_copy():
    """It should copy structs used as fields by default"""

    class Image(BaseStruct):
        path: str

        def __hash__(self):
            return id(self)

    class Item(BaseStruct):
        images: set[Image]

    image_1 = Image(path='my_image1.png')
    image_2 = Image(path='my_image2.png')

    item = Item(images={image_1, image_2})
    assert image_1 in item.images

    assert id(image_1) in {id(image) for image in item.images}
    assert id(image_2) in {id(image) for image in item.images}


def test_mapping_subclass_as_input():
    class CustomMap(dict):
        pass

    class Struct(BaseStruct):
        x: Mapping[str, int]

    d = CustomMap()
    d['one'] = 1
    d['two'] = 2

    v = Struct(x=d).x
    # we don't promise that this will or will not be a CustomMap
    # all we promise is that it _will_ be a mapping
    assert isinstance(v, Mapping)
    # but the current behavior is that it will be a dict, not a CustomMap
    # so document that here
    assert not isinstance(v, CustomMap)
    assert v == {'one': 1, 'two': 2}


def test_typing_coercion_dict():
    class Struct(BaseStruct):
        x: dict[str, int]

    m = Struct(x={'one': 1, 'two': 2})
    assert repr(m) == "Struct(x={'one': 1, 'two': 2})"


KT = TypeVar('KT')
VT = TypeVar('VT')


class MyDict(dict[KT, VT]):
    def __repr__(self):
        return f'MyDict({super().__repr__()})'


def test_class_kwargs_config():
    class Base(BaseStruct, extra='forbid', alias_generator=str.upper):
        a: int

    assert Base.model_config['extra'] == 'forbid'
    assert Base.model_config['alias_generator'] is str.upper
    # assert struct_fields(Base)['a'].alias == 'A'

    class Struct(Base, extra='allow'):
        b: int

    assert Struct.model_config['extra'] == 'allow'  # overwritten as intended
    assert Struct.model_config['alias_generator'] is str.upper  # inherited as intended
    # assert struct_fields(Struct)['b'].alias == 'B'  # alias_generator still works


def test_class_kwargs_config_and_attr_conflict():
    class Struct(BaseStruct, extra='allow', alias_generator=str.upper):
        model_config = ConfigDict(extra='forbid', title='Foobar')
        b: int

    assert Struct.model_config['extra'] == 'allow'
    assert Struct.model_config['alias_generator'] is str.upper
    assert Struct.model_config['title'] == 'Foobar'


def test_class_kwargs_custom_config():
    if platform.python_implementation() == 'PyPy':
        msg = r"__init_subclass__\(\) got an unexpected keyword argument 'some_config'"
    else:
        msg = r'__init_subclass__\(\) takes no keyword arguments'
    with pytest.raises(TypeError, match=msg):

        class Struct(BaseStruct, some_config='new_value'):
            a: int


def test_new_union_origin():
    """On 3.10+, origin of `int | str` is `types.UnionType`, not `typing.Union`"""

    class Struct(BaseStruct):
        x: 'int | str'

    assert Struct(x=3).x == 3
    assert Struct(x='3').x == '3'
    assert Struct(x='pika').x == 'pika'
    assert Struct.model_json_schema() == {
        'title': 'Struct',
        'type': 'object',
        'properties': {'x': {'title': 'X', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
        'required': ['x'],
    }


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
@pytest.mark.parametrize(
    'value',
    [None, Field()],
    ids=['none', 'field'],
)
def test_frozen_field_decl_without_default_val(ann, value):
    class Struct(BaseStruct):
        a: ann

        if value is not None:
            a = value

    assert 'a' not in Struct.__class_vars__
    assert 'a' in struct_fields(Struct)

    assert struct_fields(Struct)['a'].frozen


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
def test_deprecated_final_field_decl_with_default_val(ann):
    with pytest.warns(PydanticDeprecatedSince211):

        class Struct(BaseStruct):
            a: ann = 10

    assert 'a' in Struct.__class_vars__
    assert 'a' not in struct_fields(Struct)


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
def test_deprecated_annotated_final_field_decl_with_default_val(ann):
    with pytest.warns(PydanticDeprecatedSince211):

        class Struct(BaseStruct):
            a: Annotated[ann, ...] = 10

    assert 'a' in Struct.__class_vars__
    assert 'a' not in struct_fields(Struct)


@pytest.mark.xfail(reason="When rebuilding fields, we don't consider the field as a class variable")
def test_deprecated_final_field_with_default_val_rebuild():
    class Struct(BaseStruct):
        a: 'Final[MyInt]' = 1

    MyInt = int

    Struct.model_rebuild()

    assert 'a' in Struct.__class_vars__
    assert 'a' not in struct_fields(Struct)


def test_final_field_reassignment():
    class Struct(BaseStruct):
        model_config = ConfigDict(validate_assignment=True)

        a: Final[int]

    obj = Struct(a=10)

    with pytest.raises(ValidationError) as exc_info:
        obj.a = 20
    assert exc_info.value.errors(include_url=False) == [
        {'input': 20, 'loc': ('a',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]


def test_field_by_default_is_not_frozen():
    class Struct(BaseStruct):
        a: int

    assert not struct_fields(Struct)['a'].frozen


def test_annotated_final():
    class Struct(BaseStruct):
        a: Annotated[Final[int], Field(title='abc')]

    assert struct_fields(Struct)['a'].frozen
    assert struct_fields(Struct)['a'].title == 'abc'

    class Struct2(BaseStruct):
        a: Final[Annotated[int, Field(title='def')]]

    assert struct_fields(Struct2)['a'].frozen
    assert struct_fields(Struct2)['a'].title == 'def'


def test_post_init():
    calls = []

    class InnerStruct(BaseStruct):
        a: int
        b: int

        def model_post_init(self, context, /) -> None:
            super().model_post_init(context)  # this is included just to show it doesn't error
            assert to_python(self) == {'a': 3, 'b': 4}
            calls.append('inner_model_post_init')

    class Struct(BaseStruct):
        c: int
        d: int
        sub: InnerStruct

        def model_post_init(self, context, /) -> None:
            assert to_python(self) == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}
            calls.append('model_post_init')

    m = Struct(c=1, d='2', sub={'a': 3, 'b': '4'})
    assert calls == ['inner_model_post_init', 'model_post_init']
    assert to_python(m) == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}

    class SubStruct(Struct):
        def model_post_init(self, context, /) -> None:
            assert to_python(self) == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}
            super().model_post_init(context)
            calls.append('submodel_post_init')

    calls.clear()
    m = SubStruct(c=1, d='2', sub={'a': 3, 'b': '4'})
    assert calls == ['inner_model_post_init', 'model_post_init', 'submodel_post_init']
    assert to_python(m) == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}


def test_post_init_function_attrs_preserved() -> None:
    class Struct(BaseStruct):
        _a: int  # Necessary to have model_post_init wrapped

        def model_post_init(self, context, /) -> None:
            """Custom docstring"""

    assert Struct.model_post_init.__doc__ == 'Custom docstring'


@pytest.mark.parametrize('include_private_attribute', [True, False])
def test_post_init_call_signatures(include_private_attribute):
    calls = []

    class Struct(BaseStruct):
        a: int
        b: int
        if include_private_attribute:
            _x: int = PrivateAttr(1)

        def model_post_init(self, *args, **kwargs) -> None:
            calls.append((args, kwargs))

    Struct(a=1, b=2)
    assert calls == [((None,), {})]
    Struct.struct_construct(a=3, b=4)
    assert calls == [((None,), {}), ((None,), {})]


def test_post_init_not_called_without_override():
    calls = []

    def monkey_patched_model_post_init(cls, __context):
        calls.append('BaseStruct.model_post_init')

    original_base_model_post_init = BaseStruct.model_post_init
    try:
        BaseStruct.model_post_init = monkey_patched_model_post_init

        class WithoutOverrideStruct(BaseStruct):
            pass

        WithoutOverrideStruct()
        WithoutOverrideStruct.struct_construct()
        assert calls == []

        class WithOverrideStruct(BaseStruct):
            def model_post_init(self, context: Any, /) -> None:
                calls.append('WithOverrideStruct.model_post_init')

        WithOverrideStruct()
        assert calls == ['WithOverrideStruct.model_post_init']
        WithOverrideStruct.struct_construct()
        assert calls == ['WithOverrideStruct.model_post_init', 'WithOverrideStruct.model_post_init']

    finally:
        BaseStruct.model_post_init = original_base_model_post_init


def test_model_post_init_subclass_private_attrs():
    """https://github.com/pydantic/pydantic/issues/7293"""
    calls = []

    class A(BaseStruct):
        a: int = 1

        def model_post_init(self, context: Any, /) -> None:
            calls.append(f'{self.__class__.__name__}.model_post_init')

    class B(A):
        pass

    class C(B):
        _private: bool = True

    C()

    assert calls == ['C.model_post_init']


def test_model_post_init_supertype_private_attrs():
    """https://github.com/pydantic/pydantic/issues/9098"""

    class Struct(BaseStruct):
        _private: int = 12

    class SubStruct(Struct):
        def model_post_init(self, context: Any, /) -> None:
            if self._private == 12:
                self._private = 13
            super().model_post_init(context)

    m = SubStruct()

    assert m._private == 13


def test_model_post_init_subclass_setting_private_attrs():
    """https://github.com/pydantic/pydantic/issues/7091"""

    class Struct(BaseStruct):
        _priv1: int = PrivateAttr(91)
        _priv2: int = PrivateAttr(92)

        def model_post_init(self, context, /) -> None:
            self._priv1 = 100

    class SubStruct(Struct):
        _priv3: int = PrivateAttr(93)
        _priv4: int = PrivateAttr(94)
        _priv5: int = PrivateAttr()
        _priv6: int = PrivateAttr()

        def model_post_init(self, context, /) -> None:
            self._priv3 = 200
            self._priv5 = 300
            super().model_post_init(context)

    m = SubStruct()

    assert m._priv1 == 100
    assert m._priv2 == 92
    assert m._priv3 == 200
    assert m._priv4 == 94
    assert m._priv5 == 300
    with pytest.raises(AttributeError):
        assert m._priv6 == 94


def test_model_post_init_correct_mro():
    """https://github.com/pydantic/pydantic/issues/7293"""
    calls = []

    class A(BaseStruct):
        a: int = 1

    class B(BaseStruct):
        b: int = 1

        def model_post_init(self, context: Any, /) -> None:
            calls.append(f'{self.__class__.__name__}.model_post_init')

    class C(A, B):
        _private: bool = True

    C()

    assert calls == ['C.model_post_init']


def test_model_post_init_mocked_setattr() -> None:
    """https://github.com/pydantic/pydantic/issues/11646

    Fixes a small regression in 2.11. To instantiate private attributes on struct instances
    (and as such the `__pydantic_private__` instance attribute), Pydantic defines its own
    `model_post_init()` (and wraps the user-defined one if it exists). In tests, some users
    can mock their `model_post_init()` if they want to avoid unwanted side-effects (meaning
    `__pydantic_private__` won't be instantiated).
    In 2.11, the `BaseStruct.__setattr__` logic was tweaked and required the `__pydantic_private__`
    attribute to be present, resulting in attribute errors.
    """

    class Struct(BaseStruct):
        _a: int

        def model_post_init(self, context: Any, /) -> None:
            """Do some stuff"""

    # This reproduces `patch.object(Struct, 'model_post_init')`:
    Struct.model_post_init = lambda *args, **kwargs: None

    m = Struct()
    assert m.__pydantic_private__ is None

    m._a = 2
    assert m._a == 2


def test_del_struct_attr():
    class Struct(BaseStruct):
        some_field: str

    m = Struct(some_field='value')
    assert hasattr(m, 'some_field')

    del m.some_field

    assert not hasattr(m, 'some_field')


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy',
    reason='In this single case `del` behaves weird on pypy',
)
def test_del_struct_attr_error():
    class Struct(BaseStruct):
        some_field: str

    m = Struct(some_field='value')
    assert not hasattr(m, 'other_field')

    with pytest.raises(AttributeError, match='other_field'):
        del m.other_field


def test_del_struct_attr_with_private_attrs():
    class Struct(BaseStruct):
        _private_attr: int = PrivateAttr(default=1)
        some_field: str

    m = Struct(some_field='value')
    assert hasattr(m, 'some_field')

    del m.some_field

    assert not hasattr(m, 'some_field')


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy',
    reason='In this single case `del` behaves weird on pypy',
)
def test_del_struct_attr_with_private_attrs_error():
    class Struct(BaseStruct):
        _private_attr: int = PrivateAttr(default=1)
        some_field: str

    m = Struct(some_field='value')
    assert not hasattr(m, 'other_field')

    with pytest.raises(AttributeError, match="'Struct' object has no attribute 'other_field'"):
        del m.other_field


def test_del_struct_attr_with_private_attrs_twice_error():
    class Struct(BaseStruct):
        _private_attr: int = 1
        some_field: str

    m = Struct(some_field='value')
    assert hasattr(m, '_private_attr')

    del m._private_attr

    with pytest.raises(AttributeError, match="'Struct' object has no attribute '_private_attr'"):
        del m._private_attr


def test_deeper_recursive_struct():
    class A(BaseStruct):
        b: 'B'

    class B(BaseStruct):
        c: 'C'

    class C(BaseStruct):
        a: Optional['A']

    A.model_rebuild()
    B.model_rebuild()
    C.model_rebuild()

    m = A(b=B(c=C(a=None)))
    assert to_python(m) == {'b': {'c': {'a': None}}}


def test_model_rebuild_localns():
    class A(BaseStruct):
        x: int

    class B(BaseStruct):
        a: 'Struct'  # noqa: F821

    B.model_rebuild(_types_namespace={'Struct': A})

    m = B(a={'x': 1})
    assert to_python(m) == {'a': {'x': 1}}
    assert isinstance(m.a, A)

    class C(BaseStruct):
        a: 'Struct'  # noqa: F821

    with pytest.raises(PydanticUndefinedAnnotation, match="name 'Struct' is not defined"):
        C.model_rebuild(_types_namespace={'A': A})


def test_model_rebuild_zero_depth():
    class Struct(BaseStruct):
        x: 'X_Type'

    X_Type = str

    with pytest.raises(NameError, match='X_Type'):
        Struct.model_rebuild(_parent_namespace_depth=0)

    Struct.__pydantic_parent_namespace__.update({'X_Type': int})
    Struct.model_rebuild(_parent_namespace_depth=0)

    m = Struct(x=42)
    assert to_python(m) == {'x': 42}


@pytest.fixture(scope='session', name='InnerEqualityStruct')
def inner_equality_fixture():
    class InnerEqualityStruct(BaseStruct):
        iw: int
        ix: int = 0
        _iy: int = PrivateAttr()
        _iz: int = PrivateAttr(0)

    return InnerEqualityStruct


@pytest.fixture(scope='session', name='EqualityStruct')
def equality_fixture(InnerEqualityStruct):
    class EqualityStruct(BaseStruct):
        w: int
        x: int = 0
        _y: int = PrivateAttr()
        _z: int = PrivateAttr(0)

        struct: InnerEqualityStruct

    return EqualityStruct


def test_struct_equality(EqualityStruct, InnerEqualityStruct):
    m1 = EqualityStruct(w=0, x=0, struct=InnerEqualityStruct(iw=0))
    m2 = EqualityStruct(w=0, x=0, struct=InnerEqualityStruct(iw=0))
    assert m1 == m2


def test_struct_equality_type(EqualityStruct, InnerEqualityStruct):
    class Struct1(BaseStruct):
        x: int

    class Struct2(BaseStruct):
        x: int

    m1 = Struct1(x=1)
    m2 = Struct2(x=1)

    assert to_python(m1) == to_python(m2)
    assert m1 != m2


def test_struct_equality_dump(EqualityStruct, InnerEqualityStruct):
    inner_struct = InnerEqualityStruct(iw=0)
    assert inner_struct != to_python(inner_struct)

    struct = EqualityStruct(w=0, x=0, struct=inner_struct)
    assert struct != dict(struct)
    assert dict(struct) != to_python(struct)  # Due to presence of inner struct


def test_struct_equality_fields_set(InnerEqualityStruct):
    m1 = InnerEqualityStruct(iw=0)
    m2 = InnerEqualityStruct(iw=0, ix=0)
    assert m1.model_fields_set != m2.model_fields_set
    assert m1 == m2


def test_struct_equality_private_attrs(InnerEqualityStruct):
    m = InnerEqualityStruct(iw=0, ix=0)

    m1 = m.struct_copy()
    m2 = m.struct_copy()
    m3 = m.struct_copy()

    m2._iy = 1
    m3._iz = 1

    structs = [m1, m2, m3]
    for i, first_struct in enumerate(structs):
        for j, second_struct in enumerate(structs):
            if i == j:
                assert first_struct == second_struct
            else:
                assert first_struct != second_struct

    m2_equal = m.struct_copy()
    m2_equal._iy = 1
    assert m2 == m2_equal

    m3_equal = m.struct_copy()
    m3_equal._iz = 1
    assert m3 == m3_equal


def test_struct_copy_extra():
    class Struct(BaseStruct, extra='allow'):
        x: int

    m = Struct(x=1, y=2)
    assert to_python(m) == {'x': 1, 'y': 2}
    assert m.model_extra == {'y': 2}
    m2 = m.struct_copy()
    assert to_python(m2) == {'x': 1, 'y': 2}
    assert m2.model_extra == {'y': 2}

    m3 = m.struct_copy(update={'x': 4, 'z': 3})
    assert to_python(m3) == {'x': 4, 'y': 2, 'z': 3}
    assert m3.model_extra == {'y': 2, 'z': 3}

    m4 = m.struct_copy(update={'x': 4, 'z': 3})
    assert to_python(m4) == {'x': 4, 'y': 2, 'z': 3}
    assert m4.model_extra == {'y': 2, 'z': 3}

    m = Struct(x=1, a=2)
    m.__pydantic_extra__ = None
    m5 = m.struct_copy(update={'x': 4, 'b': 3})
    assert to_python(m5) == {'x': 4, 'b': 3}
    assert m5.model_extra == {'b': 3}


def test_struct_parametrized_name_not_generic():
    class Struct(BaseStruct):
        x: int

    with pytest.raises(TypeError, match='Concrete names should only be generated for generic structs.'):
        Struct.struct_parametrized_name(())


def test_struct_equality_generics():
    T = TypeVar('T')

    class GenericStruct(BaseStruct, Generic[T], frozen=True):
        x: T

    class ConcreteStruct(BaseStruct):
        x: int

    assert ConcreteStruct(x=1) != GenericStruct(x=1)
    assert ConcreteStruct(x=1) != GenericStruct[Any](x=1)
    assert ConcreteStruct(x=1) != GenericStruct[int](x=1)

    assert GenericStruct(x=1) != GenericStruct(x=2)

    S = TypeVar('S')
    structs = [
        GenericStruct(x=1),
        GenericStruct[S](x=1),
        GenericStruct[Any](x=1),
        GenericStruct[int](x=1),
        GenericStruct[float](x=1),
    ]
    for m1 in structs:
        for m2 in structs:
            # Test that it works with nesting as well
            m3 = GenericStruct[type(m1)](x=m1)
            m4 = GenericStruct[type(m2)](x=m2)
            assert m1 == m2
            assert m3 == m4
            assert hash(m1) == hash(m2)
            assert hash(m3) == hash(m4)


def test_struct_validate_strict() -> None:
    class LaxStruct(BaseStruct):
        x: int

        model_config = ConfigDict(strict=False)

    class StrictStruct(BaseStruct):
        x: int

        model_config = ConfigDict(strict=True)

    assert validate(LaxStruct, {'x': '1'}, strict=None) == LaxStruct(x=1)
    assert validate(LaxStruct, {'x': '1'}, strict=False) == LaxStruct(x=1)
    with pytest.raises(ValidationError) as exc_info:
        validate(LaxStruct, {'x': '1'}, strict=True)
    # there's no such thing on the struct itself
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        validate(StrictStruct, {'x': '1'})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert validate(StrictStruct, {'x': '1'}, strict=False) == StrictStruct(x=1)
    with pytest.raises(ValidationError) as exc_info:
        validate(LaxStruct, {'x': '1'}, strict=True)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


@pytest.mark.xfail(
    reason='strict=True in struct_validate_json does not overwrite strict=False given in ConfigDict'
    'See issue: https://github.com/pydantic/pydantic/issues/8930'
)
def test_struct_validate_list_strict() -> None:
    # FIXME: This change must be implemented in pydantic-core. The argument strict=True
    # in struct_validate_json method is not overwriting the one set with ConfigDict(strict=False)
    # for sequence like types. See: https://github.com/pydantic/pydantic/issues/8930

    class LaxStruct(BaseStruct):
        x: list[str]
        model_config = ConfigDict(strict=False)

    assert validate_json(LaxStruct, json.dumps({'x': ('a', 'b', 'c')}), strict=None) == LaxStruct(x=('a', 'b', 'c'))
    assert validate_json(LaxStruct, json.dumps({'x': ('a', 'b', 'c')}), strict=False) == LaxStruct(x=('a', 'b', 'c'))
    with pytest.raises(ValidationError) as exc_info:
        validate_json(LaxStruct, json.dumps({'x': ('a', 'b', 'c')}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('x',), 'msg': 'Input should be a valid list', 'input': ('a', 'b', 'c')}
    ]


def test_struct_validate_json_strict() -> None:
    class LaxStruct(BaseStruct):
        x: int

        model_config = ConfigDict(strict=False)

    class StrictStruct(BaseStruct):
        x: int

        model_config = ConfigDict(strict=True)

    assert validate_json(LaxStruct, json.dumps({'x': '1'}), strict=None) == LaxStruct(x=1)
    assert validate_json(LaxStruct, json.dumps({'x': '1'}), strict=False) == LaxStruct(x=1)
    with pytest.raises(ValidationError) as exc_info:
        validate_json(LaxStruct, json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        validate_json(StrictStruct, json.dumps({'x': '1'}), strict=None)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert validate_json(StrictStruct, json.dumps({'x': '1'}), strict=False) == StrictStruct(x=1)
    with pytest.raises(ValidationError) as exc_info:
        validate_json(StrictStruct, json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_validate_python_context() -> None:
    contexts: list[Any] = [None, None, {'foo': 'bar'}]

    class Struct(BaseStruct):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    validate(Struct, {'x': 1})
    validate(Struct, {'x': 1}, context=None)
    validate(Struct, {'x': 1}, context={'foo': 'bar'})
    assert contexts == []


def test_validate_json_context() -> None:
    contexts: list[Any] = [None, None, {'foo': 'bar'}]

    class Struct(BaseStruct):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    validate(Struct, json.dumps({'x': 1}))
    validate(Struct, json.dumps({'x': 1}), context=None)
    validate(Struct, json.dumps({'x': 1}), context={'foo': 'bar'})
    assert contexts == []


def test_struct_validate_with_validate_fn_override() -> None:
    class Struct(BaseStruct):
        a: float

    assert validate(Struct, {'a': 0.2, 'b': 0.1}) == Struct(a=0.2)

    allow = validate(Struct, {'a': 0.2, 'b': 0.1}, extra='allow')
    assert allow.model_extra == {'b': 0.1}

    with pytest.raises(ValidationError) as exc_info:
        validate(Struct, {'a': 0.2, 'b': 0.1}, extra='forbid')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('b',), 'msg': 'Extra inputs are not permitted', 'input': 0.1}
    ]


def test_struct_validate_json_with_validate_fn_override() -> None:
    class Struct(BaseStruct):
        a: float

    assert validate_json(Struct, '{"a": 0.2, "b": 0.1}') == Struct(a=0.2)

    allow = validate_json(Struct, '{"a": 0.2, "b": 0.1}', extra='allow')
    assert allow.model_extra == {'b': 0.1}

    with pytest.raises(ValidationError) as exc_info:
        validate_json(Struct, '{"a": 0.2, "b": 0.1}', extra='forbid')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('b',), 'msg': 'Extra inputs are not permitted', 'input': 0.1}
    ]


def test_struct_validate_strings_with_validate_fn_override() -> None:
    class Struct(BaseStruct):
        a: float

    assert validate_strings(Struct, {'a': '0.2', 'b': '0.1'}) == Struct(a=0.2)

    allow = validate_strings(Struct, {'a': '0.2', 'b': '0.1'}, extra='allow')
    assert allow.model_extra == {'b': '0.1'}

    with pytest.raises(ValidationError) as exc_info:
        validate_strings(Struct, {'a': '0.2', 'b': '0.1'}, extra='forbid')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('b',), 'msg': 'Extra inputs are not permitted', 'input': '0.1'}
    ]


def test_pydantic_hooks() -> None:
    calls = []

    class MyStruct(BaseStruct):
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()  # can't pass kwargs to object.__init_subclass__, weirdly
            calls.append((cls.__name__, '__init_subclass__', kwargs))

        @classmethod
        def __pydantic_init_subclass__(cls, **kwargs):
            super().__pydantic_init_subclass__(**kwargs)
            calls.append((cls.__name__, '__pydantic_init_subclass__', kwargs))

        @classmethod
        def __pydantic_on_complete__(cls):
            calls.append((cls.__name__, '__pydantic_on_complete__', 'MyStruct'))

    assert MyStruct.__pydantic_complete__
    assert MyStruct.__pydantic_fields_complete__
    assert calls == [
        ('MyStruct', '__pydantic_on_complete__', 'MyStruct'),
    ]
    calls = []

    class MySubStruct(MyStruct, a=1):
        sub: 'MySubSubStruct'

        @classmethod
        def __pydantic_on_complete__(cls):
            calls.append((cls.__name__, '__pydantic_on_complete__', 'MySubStruct'))

    assert not MySubStruct.__pydantic_complete__
    assert not MySubStruct.__pydantic_fields_complete__
    assert calls == [
        ('MySubStruct', '__init_subclass__', {'a': 1}),
        ('MySubStruct', '__pydantic_init_subclass__', {'a': 1}),
    ]
    calls = []

    class MySubSubStruct(MySubStruct, b=1):
        @classmethod
        def __pydantic_on_complete__(cls):
            calls.append((cls.__name__, '__pydantic_on_complete__', 'MySubSubStruct'))

    assert MySubSubStruct.__pydantic_complete__
    assert MySubSubStruct.__pydantic_fields_complete__
    assert calls == [
        ('MySubSubStruct', '__init_subclass__', {'b': 1}),
        ('MySubSubStruct', '__pydantic_on_complete__', 'MySubSubStruct'),
        ('MySubSubStruct', '__pydantic_init_subclass__', {'b': 1}),
    ]
    calls = []

    MySubStruct.model_rebuild()

    assert MySubStruct.__pydantic_complete__
    assert MySubStruct.__pydantic_fields_complete__
    assert calls == [
        ('MySubStruct', '__pydantic_on_complete__', 'MySubStruct'),
    ]
    calls = []

    MyStruct.model_rebuild(force=True)
    assert calls == []


def test_struct_validate_with_context():
    class InnerStruct(BaseStruct):
        x: int

        @field_validator('x')
        def validate(cls, value, info):
            return value * info.context.get('multiplier', 1)

    class OuterStruct(BaseStruct):
        inner: InnerStruct

    assert validate(OuterStruct, {'inner': {'x': 2}}, context={'multiplier': 1}).inner.x == 2
    assert validate(OuterStruct, {'inner': {'x': 2}}, context={'multiplier': 2}).inner.x == 4
    assert validate(OuterStruct, {'inner': {'x': 2}}, context={'multiplier': 3}).inner.x == 6


def test_extra_equality():
    class MyStruct(BaseStruct, extra='allow'):
        pass

    assert MyStruct(x=1) != MyStruct()


def test_equality_delegation():
    from unittest.mock import ANY

    class MyStruct(BaseStruct):
        foo: str

    assert MyStruct(foo='bar') == ANY


def test_recursion_loop_error():
    class Struct(BaseStruct):
        x: list['Struct']

    data = {'x': []}
    data['x'].append(data)
    with pytest.raises(ValidationError) as exc_info:
        Struct(**data)
    assert repr(exc_info.value.errors(include_url=False)[0]) == (
        "{'type': 'recursion_loop', 'loc': ('x', 0, 'x', 0), 'msg': "
        "'Recursion error - cyclic reference detected', 'input': {'x': [{...}]}}"
    )


def test_custom_protected_namespace():
    with pytest.warns(UserWarning, match="Field 'test_field' in 'Struct' conflicts with protected namespace 'test_'"):

        class Struct(BaseStruct):
            # this field won't raise error because we changed the default value for the
            # `protected_namespaces` config.
            struct_prefixed_field: str
            test_field: str

            model_config = ConfigDict(protected_namespaces=('test_',))


def test_multiple_protected_namespace():
    with pytest.warns(
        UserWarning,
        match=(
            r"Field 'also_protect_field' in 'Struct' conflicts with protected namespace 'also_protect_'\.\n\n"
            "You may be able to solve this by setting the 'protected_namespaces' configuration to "
            r"\('protect_me_', re.compile\('re_protect'\)\)\."
        ),
    ):

        class Struct(BaseStruct):
            also_protect_field: str

            model_config = ConfigDict(protected_namespaces=('protect_me_', 'also_protect_', re.compile('re_protect')))


def test_protected_namespace_pattern() -> None:
    with pytest.warns(UserWarning, match=r"Field 'perfect_match' in 'Struct' conflicts with protected namespace .*"):

        class Struct(BaseStruct):
            perfect_match: str

            model_config = ConfigDict(protected_namespaces=(re.compile(r'^perfect_match$'),))


def test_struct_get_core_schema() -> None:
    class Struct(BaseStruct):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(int)
            schema.pop('metadata', None)  # we don't care about this in tests
            assert schema == {'type': 'int'}
            schema = handler.generate_schema(int)
            schema.pop('metadata', None)  # we don't care about this in tests
            assert schema == {'type': 'int'}
            return handler(source_type)

    Struct()


def test_nested_types_ignored():
    from pydantic.experimental.structs import BaseStruct

    class NonNestedType:
        pass

    # Defining a nested type does not error
    class GoodStruct(BaseStruct):
        class NestedType:
            pass

        # You can still store such types on the class by annotating as a ClassVar
        MyType: ClassVar[type[Any]] = NonNestedType

        # For documentation: you _can_ give multiple names to a nested type and it won't error:
        # It might be better if it did, but this seems to be rare enough that I'm not concerned
        x = NestedType

    assert GoodStruct.MyType is NonNestedType
    assert GoodStruct.x is GoodStruct.NestedType

    with pytest.raises(PydanticUserError, match='A non-annotated attribute was detected'):

        class BadStruct(BaseStruct):
            x = NonNestedType


def test_validate_python_from_attributes() -> None:
    class Struct(BaseStruct):
        x: int

    class StructFromAttributesTrue(Struct):
        model_config = ConfigDict(from_attributes=True)

    class StructFromAttributesFalse(Struct):
        model_config = ConfigDict(from_attributes=False)

    @dataclass
    class UnrelatedClass:
        x: int = 1

    input = UnrelatedClass(1)

    for from_attributes in (False, None):
        with pytest.raises(ValidationError) as exc_info:
            validate(Struct, UnrelatedClass(), from_attributes=from_attributes)
        assert exc_info.value.errors(include_url=False) == [
            {
                'type': 'struct_type',
                'loc': (),
                'msg': 'Input should be a valid dictionary or instance of Struct',
                'input': input,
                'ctx': {'class_name': 'Struct'},
            }
        ]

    res = validate(Struct, UnrelatedClass(), from_attributes=True)
    assert res == Struct(x=1)

    with pytest.raises(ValidationError) as exc_info:
        validate(StructFromAttributesTrue, UnrelatedClass(), from_attributes=False)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'struct_type',
            'loc': (),
            'msg': 'Input should be a valid dictionary or instance of StructFromAttributesTrue',
            'input': input,
            'ctx': {'class_name': 'StructFromAttributesTrue'},
        }
    ]

    for from_attributes in (True, None):
        res = validate(StructFromAttributesTrue, UnrelatedClass(), from_attributes=from_attributes)
        assert res == StructFromAttributesTrue(x=1)

    for from_attributes in (False, None):
        with pytest.raises(ValidationError) as exc_info:
            validate(StructFromAttributesFalse, UnrelatedClass(), from_attributes=from_attributes)
        assert exc_info.value.errors(include_url=False) == [
            {
                'type': 'struct_type',
                'loc': (),
                'msg': 'Input should be a valid dictionary or instance of StructFromAttributesFalse',
                'input': input,
                'ctx': {'class_name': 'StructFromAttributesFalse'},
            }
        ]

    res = validate(StructFromAttributesFalse, UnrelatedClass(), from_attributes=True)
    assert res == StructFromAttributesFalse(x=1)


@pytest.mark.parametrize(
    'field_type,input_value,expected,raises_match,strict',
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
def test_struct_validate_strings(field_type, input_value, expected, raises_match, strict):
    class Struct(BaseStruct):
        x: field_type

    if raises_match is not None:
        with pytest.raises(expected, match=raises_match):
            validate_strings(Struct, {'x': input_value}, strict=strict)
    else:
        assert validate_strings(Struct, {'x': input_value}, strict=strict).x == expected


@pytest.mark.parametrize('strict', [True, False])
def test_struct_validate_strings_dict(strict):
    class Struct(BaseStruct):
        x: dict[int, date]

    assert validate_strings(Struct, {'x': {'1': '2017-01-01', '2': '2017-01-02'}}, strict=strict).x == {
        1: date(2017, 1, 1),
        2: date(2017, 1, 2),
    }


def test_struct_signature_annotated() -> None:
    class Struct(BaseStruct):
        x: Annotated[int, 123]

    # we used to accidentally convert `__metadata__` to a list
    # which caused things like `typing.get_args()` to fail
    assert Struct.__signature__.parameters['x'].annotation.__metadata__ == (123,)


def test_get_core_schema_unpacks_refs_for_source_type() -> None:
    # use a list to track since we end up calling `__get_pydantic_core_schema__` multiple times for structs
    # e.g. InnerStruct.__get_pydantic_core_schema__ gets called:
    # 1. When InnerStruct is defined
    # 2. When OuterStruct is defined
    # 3. When we use the TypeAdapter
    received_schemas: dict[str, list[str]] = defaultdict(list)

    @dataclass
    class Marker:
        name: str

        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas[self.name].append(schema['type'])
            return schema

    class InnerStruct(BaseStruct):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas['InnerStruct'].append(schema['type'])
            schema['metadata'] = schema.get('metadata', {})
            schema['metadata']['foo'] = 'inner was here!'
            return deepcopy(schema)

    class OuterStruct(BaseStruct):
        inner: Annotated[InnerStruct, Marker('Marker("inner")')]

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas['OuterStruct'].append(schema['type'])
            return schema

    ta = TypeAdapter(Annotated[OuterStruct, Marker('Marker("outer")')])

    # super hacky check but it works in all cases and avoids a complex and fragile iteration over CoreSchema
    # the point here is to verify that `__get_pydantic_core_schema__`
    assert 'inner was here' in str(ta.core_schema)

    assert received_schemas == {
        'InnerStruct': ['struct', 'struct'],
        'Marker("inner")': ['definition-ref'],
        'OuterStruct': ['struct', 'struct'],
        'Marker("outer")': ['definition-ref'],
    }


def test_get_core_schema_return_new_ref() -> None:
    class InnerStruct(BaseStruct):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            schema = deepcopy(schema)
            schema['metadata'] = schema.get('metadata', {})
            schema['metadata']['foo'] = 'inner was here!'
            return deepcopy(schema)

    class OuterStruct(BaseStruct):
        inner: InnerStruct
        x: int = 1

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)

            def set_x(m: 'OuterStruct') -> 'OuterStruct':
                m.x += 1
                return m

            return core_schema.no_info_after_validator_function(set_x, schema, ref=schema.pop('ref'))

    cs = OuterStruct.__pydantic_core_schema__
    # super hacky check but it works in all cases and avoids a complex and fragile iteration over CoreSchema
    # the point here is to verify that `__get_pydantic_core_schema__`
    assert 'inner was here' in str(cs)

    assert OuterStruct(inner=InnerStruct()).x == 2


def test_resolve_def_schema_from_core_schema() -> None:
    class Inner(BaseStruct):
        x: int

    class Marker:
        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            resolved = handler.resolve_ref_schema(schema)
            assert resolved['type'] == 'struct'
            assert resolved['cls'] is Inner

            def modify_inner(v: Inner) -> Inner:
                v.x += 1
                return v

            return core_schema.no_info_after_validator_function(modify_inner, schema)

    class Outer(BaseStruct):
        inner: Annotated[Inner, Marker()]

    assert validate(Outer, {'inner': {'x': 1}}).inner.x == 2


def test_extra_validator_scalar() -> None:
    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')

    class Child(Struct):
        __pydantic_extra__: dict[str, int]

    m = Child(a='1')
    assert m.__pydantic_extra__ == {'a': 1}

    # insert_assert(Child.model_json_schema())
    assert Child.model_json_schema() == {
        'additionalProperties': {'type': 'integer'},
        'properties': {},
        'title': 'Child',
        'type': 'object',
    }


def test_extra_validator_keys() -> None:
    class Struct(BaseStruct, extra='allow'):
        __pydantic_extra__: dict[Annotated[str, Field(max_length=3)], int]

    with pytest.raises(ValidationError) as exc_info:
        Struct(extra_too_long=1)

    assert exc_info.value.errors()[0]['type'] == 'string_too_long'


def test_extra_validator_field() -> None:
    class Struct(BaseStruct, extra='allow'):
        # use Field(init=False) to ensure this is not treated as a field by dataclass_transform
        __pydantic_extra__: dict[str, int] = Field(init=False)

    m = Struct(a='1')
    assert m.__pydantic_extra__ == {'a': 1}

    with pytest.raises(ValidationError) as exc_info:
        Struct(a='a')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]

    # insert_assert(Child.model_json_schema())
    assert Struct.model_json_schema() == {
        'additionalProperties': {'type': 'integer'},
        'properties': {},
        'title': 'Struct',
        'type': 'object',
    }


def test_extra_validator_named() -> None:
    class Foo(BaseStruct):
        x: int

    class Struct(BaseStruct):
        model_config = ConfigDict(extra='allow')
        __pydantic_extra__: 'dict[str, Foo]'

    class Child(Struct):
        y: int

    m = Child(a={'x': '1'}, y=2)
    assert m.__pydantic_extra__ == {'a': Foo(x=1)}

    # insert_assert(Child.model_json_schema())
    assert Child.model_json_schema() == {
        '$defs': {
            'Foo': {
                'properties': {'x': {'title': 'X', 'type': 'integer'}},
                'required': ['x'],
                'title': 'Foo',
                'type': 'object',
            }
        },
        'additionalProperties': {'$ref': '#/$defs/Foo'},
        'properties': {'y': {'title': 'Y', 'type': 'integer'}},
        'required': ['y'],
        'title': 'Child',
        'type': 'object',
    }


def test_super_getattr_extra():
    class Struct(BaseStruct):
        model_config = {'extra': 'allow'}

        def __getattr__(self, item):
            if item == 'test':
                return 'success'
            return super().__getattr__(item)

    m = Struct(x=1)
    assert m.x == 1
    with pytest.raises(AttributeError):
        m.y
    assert m.test == 'success'


def test_super_getattr_private():
    class Struct(BaseStruct):
        _x: int = PrivateAttr()

        def __getattr__(self, item):
            if item == 'test':
                return 'success'
            else:
                return super().__getattr__(item)

    m = Struct()
    m._x = 1
    assert m._x == 1
    with pytest.raises(AttributeError):
        m._y
    assert m.test == 'success'


def test_super_delattr_extra():
    test_calls = []

    class Struct(BaseStruct):
        model_config = {'extra': 'allow'}

        def __delattr__(self, item):
            if item == 'test':
                test_calls.append('success')
            else:
                super().__delattr__(item)

    m = Struct(x=1)
    assert m.x == 1
    del m.x
    with pytest.raises(AttributeError):
        m._x
    assert test_calls == []
    del m.test
    assert test_calls == ['success']


def test_super_delattr_private():
    test_calls = []

    class Struct(BaseStruct):
        _x: int = PrivateAttr()

        def __delattr__(self, item):
            if item == 'test':
                test_calls.append('success')
            else:
                super().__delattr__(item)

    m = Struct()
    m._x = 1
    assert m._x == 1
    del m._x
    with pytest.raises(AttributeError):
        m._x
    assert test_calls == []
    del m.test
    assert test_calls == ['success']


def test_arbitrary_types_not_a_type() -> None:
    """https://github.com/pydantic/pydantic/issues/6477"""

    class Foo:
        pass

    class Bar:
        pass

    with pytest.warns(UserWarning, match='is not a Python type'):
        ta = TypeAdapter(Foo(), config=ConfigDict(arbitrary_types_allowed=True))

    bar = Bar()
    assert ta.validate_python(bar) is bar


@pytest.mark.parametrize('is_dataclass', [False, True])
def test_deferred_core_schema(is_dataclass: bool) -> None:
    if is_dataclass:

        @pydantic_dataclass
        class Foo:
            x: 'Bar'
    else:

        class Foo(BaseStruct):
            x: 'Bar'

    assert isinstance(Foo.__pydantic_core_schema__, MockCoreSchema)
    with pytest.raises(PydanticUserError, match='`Foo` is not fully defined'):
        Foo.__pydantic_core_schema__['type']

    class Bar(BaseStruct):
        pass

    assert Foo.__pydantic_core_schema__['type'] == ('dataclass' if is_dataclass else 'struct')
    assert isinstance(Foo.__pydantic_core_schema__, dict)


def test_help(create_module):
    module = create_module(
        # language=Python
        """
import pydoc

from pydantic.experimental.structs import BaseStruct

class Struct(BaseStruct):
    x: int


help_result_string = pydoc.render_doc(Struct)
"""
    )
    assert 'class Struct' in module.help_result_string


def test_cannot_use_leading_underscore_field_names():
    with pytest.raises(
        NameError, match="Fields must not use names with leading underscores; e.g., use 'x' instead of '_x'"
    ):

        class Struct1(BaseStruct):
            _x: int = Field(alias='x')

    with pytest.raises(
        NameError, match="Fields must not use names with leading underscores; e.g., use 'x__' instead of '__x__'"
    ):

        class Struct2(BaseStruct):
            __x__: int = Field()

    with pytest.raises(
        NameError, match="Fields must not use names with leading underscores; e.g., use 'my_field' instead of '___'"
    ):

        class Struct3(BaseStruct):
            ___: int = Field(default=1)


def test_customize_type_constraints_order() -> None:
    class Struct(BaseStruct):
        # whitespace will be stripped first, then max length will be checked, should pass on ' 1 '
        x: Annotated[str, AfterValidator(lambda x: x.strip()), StringConstraints(max_length=1)]
        # max length will be checked first, then whitespace will be stripped, should fail on ' 1 '
        y: Annotated[str, StringConstraints(max_length=1), AfterValidator(lambda x: x.strip())]

    with pytest.raises(ValidationError) as exc_info:
        Struct(x=' 1 ', y=' 1 ')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('y',),
            'msg': 'String should have at most 1 character',
            'input': ' 1 ',
            'ctx': {'max_length': 1},
        }
    ]


def test_shadow_attribute() -> None:
    """https://github.com/pydantic/pydantic/issues/7108"""

    class Struct(BaseStruct):
        foo: str

        @classmethod
        def __pydantic_init_subclass__(cls, **kwargs: Any):
            super().__pydantic_init_subclass__(**kwargs)
            for key in struct_fields(cls).keys():
                setattr(cls, key, getattr(cls, key, '') + ' edited!')

    class One(Struct):
        foo: str = 'abc'

    with pytest.warns(UserWarning, match=r'"foo" in ".*Two" shadows an attribute in parent ".*One"'):

        class Two(One):
            foo: str

    with pytest.warns(UserWarning, match=r'"foo" in ".*Three" shadows an attribute in parent ".*One"'):

        class Three(One):
            foo: str = 'xyz'

    # unlike dataclasses BaseStruct does not preserve the value of defaults
    # so when we access the attribute in `Struct.__pydantic_init_subclass__` there is no default
    # and hence we append `edited!` to an empty string
    # we've talked about changing this but this is the current behavior as of this test
    assert getattr(Struct, 'foo', None) is None
    assert getattr(One, 'foo', None) == ' edited!'
    assert getattr(Two, 'foo', None) == ' edited! edited!'
    assert getattr(Three, 'foo', None) == ' edited! edited!'


def test_shadow_attribute_warn_for_redefined_fields() -> None:
    """https://github.com/pydantic/pydantic/issues/9107"""

    # A simple class which defines a field
    class Parent:
        foo: bool = False

    # When inheriting from the parent class, as long as the field is not defined at all, there should be no warning
    # about shadowed fields.
    with warnings.catch_warnings(record=True) as captured_warnings:
        # Start capturing all warnings
        warnings.simplefilter('always')

        class ChildWithoutRedefinedField(BaseStruct, Parent):
            pass

        # Check that no warnings were captured
        assert len(captured_warnings) == 0

    # But when inheriting from the parent class and a parent field is redefined, a warning should be raised about
    # shadowed fields irrespective of whether it is defined with a type that is still compatible or narrower, or
    # with a different default that is still compatible with the type definition.
    with pytest.warns(
        UserWarning,
        match=r'"foo" in ".*ChildWithRedefinedField" shadows an attribute in parent ".*Parent"',
    ):

        class ChildWithRedefinedField(BaseStruct, Parent):
            foo: bool = True


def test_field_name_deprecated_method_name() -> None:
    """https://github.com/pydantic/pydantic/issues/11912"""

    with pytest.warns(UserWarning):

        class Struct(BaseStruct):
            # `collect_model_fields()` will special case these to not use
            # the deprecated methods as default values:
            dict: int
            schema: str

        assert struct_fields(Struct)['dict'].is_required()
        assert struct_fields(Struct)['schema'].is_required()


def test_eval_type_backport():
    class Struct(BaseStruct):
        foo: 'list[int | str]'

    assert to_python(Struct(foo=[1, '2'])) == {'foo': [1, '2']}

    with pytest.raises(ValidationError) as exc_info:
        Struct(foo='not a list')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('foo',),
            'msg': 'Input should be a valid list',
            'input': 'not a list',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        Struct(foo=[{'not a str or int'}])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_type',
            'loc': ('foo', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': {'not a str or int'},
        },
        {
            'type': 'string_type',
            'loc': ('foo', 0, 'str'),
            'msg': 'Input should be a valid string',
            'input': {'not a str or int'},
        },
    ]


def test_inherited_class_vars(create_module):
    @create_module
    def module():
        import typing

        from pydantic.experimental.structs import BaseStruct

        class Base(BaseStruct):
            CONST1: 'typing.ClassVar[str]' = 'a'
            CONST2: 'ClassVar[str]' = 'b'

    class Child(module.Base):
        pass

    assert Child.CONST1 == 'a'
    assert Child.CONST2 == 'b'


def test_schema_valid_for_inner_generic() -> None:
    T = TypeVar('T')

    class Inner(BaseStruct, Generic[T]):
        x: T

    class Outer(BaseStruct):
        inner: Inner[int]

    assert Outer(inner={'x': 1}).inner.x == 1
    # confirming that the typevars are substituted in the outer struct schema
    assert Outer.__pydantic_core_schema__['schema']['fields']['inner']['schema']['cls'] == Inner[int]
    assert (
        Outer.__pydantic_core_schema__['schema']['fields']['inner']['schema']['schema']['fields']['x']['schema']['type']
        == 'int'
    )


def test_validation_works_for_cyclical_forward_refs() -> None:
    class X(BaseStruct):
        y: Union['Y', None]

    class Y(BaseStruct):
        x: Union[X, None]

    assert Y(x={'y': None}).x.y is None


def test_struct_construct_with_model_post_init_and_struct_copy() -> None:
    class Struct(BaseStruct):
        id: int

        def model_post_init(self, context: Any, /) -> None:
            super().model_post_init(context)

    m = Struct.struct_construct(id=1)
    copy = m.struct_copy(deep=True)

    assert m == copy
    assert id(m) != id(copy)


def test_subclassing_gen_schema_warns() -> None:
    with pytest.warns(UserWarning, match='Subclassing `GenerateSchema` is not supported.'):

        class MyGenSchema(GenerateSchema): ...


@pytest.mark.skipif(sys.version_info < (3, 13), reason='requires python 3.13')
def test_replace() -> None:
    from copy import replace

    class Struct(BaseStruct):
        x: int
        y: int

    m = Struct(x=1, y=2)
    assert replace(m, x=3) == Struct(x=3, y=2)
