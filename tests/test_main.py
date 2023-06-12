import json
import platform
import re
import sys
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Set,
    Type,
    TypeVar,
    get_type_hints,
)
from uuid import UUID, uuid4

import pytest
from pydantic_core import CoreSchema, core_schema
from typing_extensions import Annotated, Final, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    PydanticUndefinedAnnotation,
    PydanticUserError,
    SecretStr,
    ValidationError,
    ValidationInfo,
    constr,
    field_validator,
)
from pydantic.type_adapter import TypeAdapter


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


@pytest.fixture(name='UltraSimpleModel', scope='session')
def ultra_simple_model_fixture():
    class UltraSimpleModel(BaseModel):
        a: float
        b: int = 10

    return UltraSimpleModel


def test_ultra_simple_missing(UltraSimpleModel):
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.errors(include_url=False) == [
        {'loc': ('a',), 'msg': 'Field required', 'type': 'missing', 'input': {}}
    ]
    assert str(exc_info.value) == (
        '1 validation error for UltraSimpleModel\n'
        'a\n'
        '  Field required [type=missing, input_value={}, input_type=dict]'
    )


def test_ultra_simple_failed(UltraSimpleModel):
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid number, unable to parse string as an number',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
    ]


def test_ultra_simple_repr(UltraSimpleModel):
    m = UltraSimpleModel(a=10.2)
    assert str(m) == 'a=10.2 b=10'
    assert repr(m) == 'UltraSimpleModel(a=10.2, b=10)'
    assert repr(m.model_fields['a']) == 'FieldInfo(annotation=float, required=True)'
    assert repr(m.model_fields['b']) == 'FieldInfo(annotation=int, required=False, default=10)'
    assert dict(m) == {'a': 10.2, 'b': 10}
    assert m.model_dump() == {'a': 10.2, 'b': 10}
    assert m.model_dump_json() == '{"a":10.2,"b":10}'
    assert str(m) == 'a=10.2 b=10'


def test_default_factory_field():
    def myfunc():
        return 1

    class Model(BaseModel):
        a: int = Field(default_factory=myfunc)

    m = Model()
    assert str(m) == 'a=1'
    assert repr(m.model_fields['a']) == 'FieldInfo(annotation=int, required=False, default_factory=myfunc)'
    assert dict(m) == {'a': 1}
    assert m.model_dump_json() == '{"a":1}'


def test_comparing(UltraSimpleModel):
    m = UltraSimpleModel(a=10.2, b='100')
    assert m.model_dump() == {'a': 10.2, 'b': 100}
    assert m != {'a': 10.2, 'b': 100}
    assert m == UltraSimpleModel(a=10.2, b=100)


@pytest.fixture(scope='session', name='NoneCheckModel')
def none_check_model_fix():
    class NoneCheckModel(BaseModel):
        existing_str_value: str = 'foo'
        required_str_value: str = ...
        required_str_none_value: Optional[str] = ...
        existing_bytes_value: bytes = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: Optional[bytes] = ...

    return NoneCheckModel


def test_nullable_strings_success(NoneCheckModel):
    m = NoneCheckModel(
        required_str_value='v1', required_str_none_value=None, required_bytes_value='v2', required_bytes_none_value=None
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails(NoneCheckModel):
    with pytest.raises(ValidationError) as exc_info:
        NoneCheckModel(
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


@pytest.fixture(name='ParentModel', scope='session')
def parent_sub_model_fixture():
    class UltraSimpleModel(BaseModel):
        a: float
        b: int = 10

    class ParentModel(BaseModel):
        grape: bool
        banana: UltraSimpleModel

    return ParentModel


def test_parent_sub_model(ParentModel):
    m = ParentModel(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == 'ParentModel(grape=True, banana=UltraSimpleModel(a=1.0, b=10))'


def test_parent_sub_model_fails(ParentModel):
    with pytest.raises(ValidationError):
        ParentModel(grape=1, banana=123)


def test_not_required():
    class Model(BaseModel):
        a: float = None

    assert Model(a=12.2).a == 12.2
    assert Model().a is None
    with pytest.raises(ValidationError) as exc_info:
        Model(a=None)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_type',
            'loc': ('a',),
            'msg': 'Input should be a valid number',
            'input': None,
        },
    ]


def test_allow_extra():
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: float

    m = Model(a='10.2', b=12)
    assert m.__dict__ == {'a': 10.2}
    assert m.__pydantic_extra__ == {'b': 12}
    assert m.a == 10.2
    assert m.b == 12
    assert m.model_extra == {'b': 12}


@pytest.mark.parametrize('extra', ['ignore', 'forbid', 'allow'])
def test_allow_extra_from_attributes(extra: Literal['ignore', 'forbid', 'allow']):
    class Model(BaseModel):
        a: float

        model_config = ConfigDict(extra=extra, from_attributes=True)

    class TestClass:
        a = 1.0
        b = 12

    m = Model.model_validate(TestClass())
    assert m.a == 1.0
    assert not hasattr(m, 'b')


def test_allow_extra_repr():
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: float = ...

    assert str(Model(a='10.2', b=12)) == 'a=10.2 b=12'


def test_forbidden_extra_success():
    class ForbiddenExtra(BaseModel):
        model_config = ConfigDict(extra='forbid')
        foo: str = 'whatever'

    m = ForbiddenExtra()
    assert m.foo == 'whatever'


def test_forbidden_extra_fails():
    class ForbiddenExtra(BaseModel):
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
    class Model(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        a: float

    model = Model(a=0.2)
    with pytest.raises(ValidationError, match=r"b\s+Object has no attribute 'b'"):
        model.b = 2


def test_assign_extra_validate():
    class Model(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        a: float

    model = Model(a=0.2)
    with pytest.raises(ValidationError, match=r"b\s+Object has no attribute 'b'"):
        model.b = 2


def test_extra_allowed():
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: float

    model = Model(a=0.2, b=0.1)
    assert model.b == 0.1

    assert not hasattr(model, 'c')
    model.c = 1
    assert hasattr(model, 'c')
    assert model.c == 1


def test_extra_ignored():
    class Model(BaseModel):
        model_config = ConfigDict(extra='ignore')
        a: float

    model = Model(a=0.2, b=0.1)
    assert not hasattr(model, 'b')

    with pytest.raises(ValueError, match='"Model" object has no field "b"'):
        model.b = 1

    assert model.model_extra is None


def test_field_order_is_preserved_with_extra():
    """This test covers https://github.com/pydantic/pydantic/issues/1234."""

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: int
        b: str
        c: float

    model = Model(a=1, b='2', c=3.0, d=4)
    assert repr(model) == "Model(a=1, b='2', c=3.0, d=4)"
    assert str(model.model_dump()) == "{'a': 1, 'b': '2', 'c': 3.0, 'd': 4}"
    assert str(model.model_dump_json()) == '{"a":1,"b":"2","c":3.0,"d":4}'


def test_extra_broken_via_pydantic_extra_interference():
    """
    At the time of writing this test there is `_model_construction.model_extra_getattr` being assigned to model's
    `__getattr__`. The method then expects `BaseModel.__pydantic_extra__` isn't `None`. Both this actions happen when
    `model_config.extra` is set to `True`. However, this behavior could be accidentally broken in a subclass of
    `BaseModel`. In that case `AttributeError` should be thrown when `__getattr__` is being accessed essentially
    disabling the `extra` functionality.
    """

    class BrokenExtraBaseModel(BaseModel):
        def model_post_init(self, __context: Any) -> None:
            super().model_post_init(__context)
            object.__setattr__(self, '__pydantic_extra__', None)

    class Model(BrokenExtraBaseModel):
        model_config = ConfigDict(extra='allow')

    m = Model(extra_field='some extra value')

    with pytest.raises(AttributeError) as e:
        m.extra_field

    assert e.value.args == ("'Model' object has no attribute 'extra_field'",)


def test_set_attr(UltraSimpleModel):
    m = UltraSimpleModel(a=10.2)
    assert m.model_dump() == {'a': 10.2, 'b': 10}

    m.b = 20
    assert m.model_dump() == {'a': 10.2, 'b': 20}


def test_set_attr_invalid():
    class UltraSimpleModel(BaseModel):
        a: float = ...
        b: int = 10

    m = UltraSimpleModel(a=10.2)
    assert m.model_dump() == {'a': 10.2, 'b': 10}

    with pytest.raises(ValueError) as exc_info:
        m.c = 20
    assert '"UltraSimpleModel" object has no field "c"' in exc_info.value.args[0]


def test_any():
    class AnyModel(BaseModel):
        a: Any = 10
        b: object = 20

    m = AnyModel()
    assert m.a == 10
    assert m.b == 20

    m = AnyModel(a='foobar', b='barfoo')
    assert m.a == 'foobar'
    assert m.b == 'barfoo'


def test_population_by_field_name():
    class Model(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        a: str = Field(alias='_a')

    assert Model(a='different').a == 'different'
    assert Model(a='different').model_dump() == {'a': 'different'}
    assert Model(a='different').model_dump(by_alias=True) == {'_a': 'different'}


def test_field_order():
    class Model(BaseModel):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    assert list(Model.model_fields.keys()) == ['c', 'b', 'a', 'd']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.model_dump() == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('a',), 'msg': 'Field required', 'input': {}}
    ]


def test_mutability():
    class TestModel(BaseModel):
        a: int = 10

        model_config = ConfigDict(extra='forbid', frozen=False)

    m = TestModel()

    assert m.a == 10
    m.a = 11
    assert m.a == 11


def test_frozen_model():
    class FrozenModel(BaseModel):
        model_config = ConfigDict(extra='forbid', frozen=True)

        a: int = 10

    m = FrozenModel()

    assert m.a == 10
    with pytest.raises(ValidationError) as exc_info:
        m.a = 11
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': ('a',), 'msg': 'Instance is frozen', 'input': 11}
    ]


def test_not_frozen_are_not_hashable():
    class TestModel(BaseModel):
        a: int = 10

    m = TestModel()
    with pytest.raises(TypeError) as exc_info:
        hash(m)
    assert "unhashable type: 'TestModel'" in exc_info.value.args[0]


def test_with_declared_hash():
    class Foo(BaseModel):
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
    class TestModel(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int = 10

    m = TestModel()
    assert m.__hash__ is not None
    assert isinstance(hash(m), int)


def test_frozen_with_unhashable_fields_are_not_hashable():
    class TestModel(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int = 10
        y: List[int] = [1, 2, 3]

    m = TestModel()
    with pytest.raises(TypeError) as exc_info:
        hash(m)
    assert "unhashable type: 'list'" in exc_info.value.args[0]


def test_hash_function_give_different_result_for_different_object():
    class TestModel(BaseModel):
        model_config = ConfigDict(frozen=True)

        a: int = 10

    m = TestModel()
    m2 = TestModel()
    m3 = TestModel(a=11)
    assert hash(m) == hash(m2)
    assert hash(m) != hash(m3)

    # Redefined `TestModel`
    class TestModel(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int = 10

    m4 = TestModel()
    assert hash(m) != hash(m4)


@pytest.fixture(name='ValidateAssignmentModel', scope='session')
def validate_assignment_fixture():
    class ValidateAssignmentModel(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        a: int = 2
        b: constr(min_length=1)

    return ValidateAssignmentModel


def test_validating_assignment_pass(ValidateAssignmentModel):
    p = ValidateAssignmentModel(a=5, b='hello')
    p.a = 2
    assert p.a == 2
    assert p.model_dump() == {'a': 2, 'b': 'hello'}
    p.b = 'hi'
    assert p.b == 'hi'
    assert p.model_dump() == {'a': 2, 'b': 'hi'}


def test_validating_assignment_fail(ValidateAssignmentModel):
    p = ValidateAssignmentModel(a=5, b='hello')

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
            'msg': 'String should have at least 1 characters',
            'input': '',
            'ctx': {'min_length': 1},
        }
    ]


def test_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Model(BaseModel):
        model_config = ConfigDict(use_enum_values=True)
        foo: FooEnum

    m = Model(foo='foo')
    # this is the actual value, so has not "values" field
    assert m.foo == FooEnum.foo
    assert isinstance(m.foo, FooEnum)


def test_literal_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo_value', 'bar': 'bar_value'})

    class Model(BaseModel):
        baz: Literal[FooEnum.foo]
        boo: str = 'hoo'
        model_config = ConfigDict(use_enum_values=True)

    m = Model(baz=FooEnum.foo)
    assert m.model_dump() == {'baz': FooEnum.foo, 'boo': 'hoo'}
    assert m.model_dump(mode='json') == {'baz': 'foo_value', 'boo': 'hoo'}
    assert m.baz.value == 'foo_value'

    with pytest.raises(ValidationError) as exc_info:
        Model(baz=FooEnum.bar)

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


def test_enum_raw():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Model(BaseModel):
        foo: FooEnum = None

    m = Model(foo='foo')
    assert isinstance(m.foo, FooEnum)
    assert m.foo != 'foo'
    assert m.foo.value == 'foo'


def test_set_tuple_values():
    class Model(BaseModel):
        foo: set
        bar: tuple

    m = Model(foo=['a', 'b'], bar=['c', 'd'])
    assert m.foo == {'a', 'b'}
    assert m.bar == ('c', 'd')
    assert m.model_dump() == {'foo': {'a', 'b'}, 'bar': ('c', 'd')}


def test_default_copy():
    class User(BaseModel):
        friends: List[int] = Field(default_factory=lambda: [])

    u1 = User()
    u2 = User()
    assert u1.friends is not u2.friends


class ArbitraryType:
    pass


def test_arbitrary_type_allowed_validation_success():
    class ArbitraryTypeAllowedModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        t: ArbitraryType

    arbitrary_type_instance = ArbitraryType()
    m = ArbitraryTypeAllowedModel(t=arbitrary_type_instance)
    assert m.t == arbitrary_type_instance


class OtherClass:
    pass


def test_arbitrary_type_allowed_validation_fails():
    class ArbitraryTypeAllowedModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        t: ArbitraryType

    input_value = OtherClass()
    with pytest.raises(ValidationError) as exc_info:
        ArbitraryTypeAllowedModel(t=input_value)
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

        class ArbitraryTypeNotAllowedModel(BaseModel):
            t: ArbitraryType


@pytest.fixture(scope='session', name='TypeTypeModel')
def type_type_model_fixture():
    class TypeTypeModel(BaseModel):
        t: Type[ArbitraryType]

    return TypeTypeModel


def test_type_type_validation_success(TypeTypeModel):
    arbitrary_type_class = ArbitraryType
    m = TypeTypeModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_subclass_validation_success(TypeTypeModel):
    class ArbitrarySubType(ArbitraryType):
        pass

    arbitrary_type_class = ArbitrarySubType
    m = TypeTypeModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


@pytest.mark.parametrize('input_value', [OtherClass, 1])
def test_type_type_validation_fails(TypeTypeModel, input_value):
    with pytest.raises(ValidationError) as exc_info:
        TypeTypeModel(t=input_value)
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


@pytest.mark.parametrize('bare_type', [type, Type])
def test_bare_type_type_validation_success(bare_type):
    class TypeTypeModel(BaseModel):
        t: bare_type

    arbitrary_type_class = ArbitraryType
    m = TypeTypeModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


@pytest.mark.parametrize('bare_type', [type, Type])
def test_bare_type_type_validation_fails(bare_type):
    class TypeTypeModel(BaseModel):
        t: bare_type

    arbitrary_type = ArbitraryType()
    with pytest.raises(ValidationError) as exc_info:
        TypeTypeModel(t=arbitrary_type)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_type',
            'loc': ('t',),
            'msg': 'Input should be a type',
            'input': arbitrary_type,
        }
    ]


def test_annotation_field_name_shadows_attribute():
    with pytest.raises(NameError):
        # When defining a model that has an attribute with the name of a built-in attribute, an exception is raised
        class BadModel(BaseModel):
            model_json_schema: str  # This conflicts with the BaseModel's model_json_schema() class method


def test_value_field_name_shadows_attribute():
    with pytest.raises(PydanticUserError, match="A non-annotated attribute was detected: `model_json_schema = 'abc'`"):

        class BadModel(BaseModel):
            model_json_schema = (
                'abc'  # This conflicts with the BaseModel's model_json_schema() class method, but has no annotation
            )


def test_class_var():
    class MyModel(BaseModel):
        a: ClassVar
        b: ClassVar[int] = 1
        c: int = 2

    assert list(MyModel.model_fields.keys()) == ['c']

    class MyOtherModel(MyModel):
        a = ''
        b = 2

    assert list(MyOtherModel.model_fields.keys()) == ['c']


def test_fields_set():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.model_fields_set == {'a'}

    m.b = 2
    assert m.model_fields_set == {'a', 'b'}

    m = MyModel(a=5, b=2)
    assert m.model_fields_set == {'a', 'b'}


def test_exclude_unset_dict():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.model_dump(exclude_unset=True) == {'a': 5}

    m = MyModel(a=5, b=3)
    assert m.model_dump(exclude_unset=True) == {'a': 5, 'b': 3}


def test_exclude_unset_recursive():
    class ModelA(BaseModel):
        a: int
        b: int = 1

    class ModelB(BaseModel):
        c: int
        d: int = 2
        e: ModelA

    m = ModelB(c=5, e={'a': 0})
    assert m.model_dump() == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert m.model_dump(exclude_unset=True) == {'c': 5, 'e': {'a': 0}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': ModelA(a=0, b=1)}


def test_dict_exclude_unset_populated_by_alias():
    class MyModel(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

    m = MyModel(alias_a='a')

    assert m.model_dump(exclude_unset=True) == {'a': 'a'}
    assert m.model_dump(exclude_unset=True, by_alias=True) == {'alias_a': 'a'}


def test_dict_exclude_unset_populated_by_alias_with_extra():
    class MyModel(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

    m = MyModel(alias_a='a', c='c')

    assert m.model_dump(exclude_unset=True) == {'a': 'a', 'c': 'c'}
    assert m.model_dump(exclude_unset=True, by_alias=True) == {'alias_a': 'a', 'c': 'c'}


def test_exclude_defaults():
    class Model(BaseModel):
        mandatory: str
        nullable_mandatory: Optional[str] = ...
        facultative: str = 'x'
        nullable_facultative: Optional[str] = None

    m = Model(mandatory='a', nullable_mandatory=None)
    assert m.model_dump(exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
    }

    m = Model(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative=None)
    assert m.model_dump(exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
        'facultative': 'y',
    }

    m = Model(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative='z')
    assert m.model_dump(exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
        'facultative': 'y',
        'nullable_facultative': 'z',
    }


def test_dir_fields():
    class MyModel(BaseModel):
        attribute_a: int
        attribute_b: int = 2

    m = MyModel(attribute_a=5)

    assert 'model_dump' in dir(m)
    assert 'model_dump_json' in dir(m)
    assert 'attribute_a' in dir(m)
    assert 'attribute_b' in dir(m)


def test_dict_with_extra_keys():
    class MyModel(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: str = Field(None, alias='alias_a')

    m = MyModel(extra_key='extra')
    assert m.model_dump() == {'a': None, 'extra_key': 'extra'}
    assert m.model_dump(by_alias=True) == {'alias_a': None, 'extra_key': 'extra'}


def test_ignored_types():
    from pydantic import BaseModel

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    class Model(BaseModel):
        model_config = ConfigDict(ignored_types=(classproperty,))

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    assert Model.class_name == 'Model'
    assert Model().class_name == 'Model'


def test_model_iteration():
    class Foo(BaseModel):
        a: int = 1
        b: int = 2

    class Bar(BaseModel):
        c: int
        d: Foo

    m = Bar(c=3, d={})
    assert m.model_dump() == {'c': 3, 'd': {'a': 1, 'b': 2}}
    assert list(m) == [('c', 3), ('d', Foo())]
    assert dict(m) == {'c': 3, 'd': Foo()}


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
def test_model_export_nested_list(exclude, expected, raises_match):
    class Foo(BaseModel):
        a: int = 1
        b: int = 2

    class Bar(BaseModel):
        c: int
        foos: List[Foo]

    m = Bar(c=3, foos=[Foo(a=1, b=2), Foo(a=3, b=4)])

    if raises_match is not None:
        with pytest.raises(expected, match=raises_match):
            m.model_dump(exclude=exclude)
    else:
        original_exclude = deepcopy(exclude)
        assert m.model_dump(exclude=exclude) == expected
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
def test_model_export_dict_exclusion(excludes, expected):
    class Foo(BaseModel):
        a: int = 1
        bars: List[Dict[str, int]]

    m = Foo(a=1, bars=[{'w': 0, 'x': 1}, {'y': 2}, {'w': -1, 'z': 3}])

    original_excludes = deepcopy(excludes)
    assert m.model_dump(exclude=excludes) == expected
    assert excludes == original_excludes


def test_field_exclude():
    class User(BaseModel):
        _priv: int = PrivateAttr()
        id: int
        username: str
        password: SecretStr = Field(exclude=True)
        hobbies: List[str]

    my_user = User(id=42, username='JohnDoe', password='hashedpassword', hobbies=['scuba diving'])

    my_user._priv = 13
    assert my_user.id == 42
    assert my_user.password.get_secret_value() == 'hashedpassword'
    assert my_user.model_dump() == {'id': 42, 'username': 'JohnDoe', 'hobbies': ['scuba diving']}


def test_revalidate_instances_never():
    class User(BaseModel):
        hobbies: List[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseModel):
        user: User

    t = Transaction(user=my_user)

    assert t.user is my_user
    assert t.user.hobbies is my_user.hobbies

    class SubUser(User):
        sins: List[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is my_sub_user
    assert t.user.hobbies is my_sub_user.hobbies


def test_revalidate_instances_sub_instances():
    class User(BaseModel, revalidate_instances='subclass-instances'):
        hobbies: List[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseModel):
        user: User

    t = Transaction(user=my_user)

    assert t.user is my_user
    assert t.user.hobbies is my_user.hobbies

    class SubUser(User):
        sins: List[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is not my_sub_user
    assert t.user.hobbies is not my_sub_user.hobbies
    assert not hasattr(t.user, 'sins')


def test_revalidate_instances_always():
    class User(BaseModel, revalidate_instances='always'):
        hobbies: List[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseModel):
        user: User

    t = Transaction(user=my_user)

    assert t.user is not my_user
    assert t.user.hobbies is not my_user.hobbies

    class SubUser(User):
        sins: List[str]

    my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])

    t = Transaction(user=my_sub_user)

    assert t.user is not my_sub_user
    assert t.user.hobbies is not my_sub_user.hobbies
    assert not hasattr(t.user, 'sins')


def test_revalidate_instances_always_list_of_model_instance():
    class A(BaseModel):
        model_config = ConfigDict(revalidate_instances='always')
        name: str

    class B(BaseModel):
        list_a: List[A]

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
def test_model_export_exclusion_with_fields_and_config(kinds, exclude, expected):
    """Test that exporting models with fields using the export parameter works."""

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

    class Sub(BaseModel):
        a: List[int] = Field([3, 4, 5], exclude={1} if 'sub_fields' in kinds else None)
        b: int = Field(4, exclude=... if 'sub_fields' in kinds else None)
        c: str = 'foobar'

        Config = ChildConfig

    class Model(BaseModel):
        a: int = 0
        b: int = Field(2, exclude=... if 'model_fields' in kinds else None)
        c: Sub = Sub()
        d: Sub = Field(Sub(), exclude={'a'} if 'model_fields' in kinds else None)

        Config = ParentConfig

    m = Model()
    assert m.model_dump(exclude=exclude) == expected, 'Unexpected model export result'


@pytest.mark.skip(reason='not implemented')
def test_model_export_exclusion_inheritance():
    class Sub(BaseModel):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = Field('v4', exclude=...)

    class Parent(BaseModel):
        model_config = ConfigDict(fields={'a': {'exclude': ...}, 's': {'exclude': {'s1'}}})
        a: int
        b: int = Field(..., exclude=...)
        c: int
        d: int
        s: Sub = Sub()

    class Child(Parent):
        model_config = ConfigDict(fields={'c': {'exclude': ...}, 's': {'exclude': {'s2'}}})

    actual = Child(a=0, b=1, c=2, d=3).model_dump()
    expected = {'d': 3, 's': {'s3': 'v3'}}
    assert actual == expected, 'Unexpected model export result'


@pytest.mark.skip(reason='not implemented')
def test_model_export_with_true_instead_of_ellipsis():
    class Sub(BaseModel):
        s1: int = 1

    class Model(BaseModel):
        model_config = ConfigDict(fields={'c': {'exclude': True}})
        a: int = 2
        b: int = Field(3, exclude=True)
        c: int = Field(4)
        s: Sub = Sub()

    m = Model()
    assert m.model_dump(exclude={'s': True}) == {'a': 2}


@pytest.mark.skip(reason='not implemented')
def test_model_export_inclusion():
    class Sub(BaseModel):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = 'v4'

    class Model(BaseModel):
        model_config = ConfigDict(
            fields={'a': {'include': {'s2', 's1', 's3'}}, 'b': {'include': {'s1', 's2', 's3', 's4'}}}
        )
        a: Sub = Sub()
        b: Sub = Field(Sub(), include={'s1'})
        c: Sub = Field(Sub(), include={'s1', 's2'})

    Model.model_fields['a'].field_info.include == {'s1': ..., 's2': ..., 's3': ...}
    Model.model_fields['b'].field_info.include == {'s1': ...}
    Model.model_fields['c'].field_info.include == {'s1': ..., 's2': ...}

    actual = Model().model_dump(include={'a': {'s3', 's4'}, 'b': ..., 'c': ...})
    # s1 included via field, s2 via config and s3 via .dict call:
    expected = {'a': {'s3': 'v3'}, 'b': {'s1': 'v1'}, 'c': {'s1': 'v1', 's2': 'v2'}}

    assert actual == expected, 'Unexpected model export result'


@pytest.mark.skip(reason='not implemented')
def test_model_export_inclusion_inheritance():
    class Sub(BaseModel):
        s1: str = Field('v1', include=...)
        s2: str = Field('v2', include=...)
        s3: str = Field('v3', include=...)
        s4: str = 'v4'

    class Parent(BaseModel):
        # b will be included since fields are set idependently
        model_config = ConfigDict(fields={'b': {'include': ...}})
        a: int
        b: int
        c: int
        s: Sub = Field(Sub(), include={'s1', 's2'})  # overrides includes set in Sub model

    class Child(Parent):
        # b is still included even if it doesn't occur here since fields
        # are still considered separately.
        # s however, is merged, resulting in only s1 being included.
        model_config = ConfigDict(fields={'a': {'include': ...}, 's': {'include': {'s1'}}})

    actual = Child(a=0, b=1, c=2).model_dump()
    expected = {'a': 0, 'b': 1, 's': {'s1': 'v1'}}
    assert actual == expected, 'Unexpected model export result'


def test_untyped_fields_warning():
    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            "A non-annotated attribute was detected: `x = 1`. All model fields require a type annotation; "
            "if `x` is not meant to be a field, you may be able to resolve this error by annotating it "
            "as a `ClassVar` or updating `model_config['ignored_types']`."
        ),
    ):

        class WarningModel(BaseModel):
            x = 1

    # Prove that annotating with ClassVar prevents the warning
    class NonWarningModel(BaseModel):
        x: ClassVar = 1


def test_untyped_fields_error():
    with pytest.raises(TypeError, match="Field 'a' requires a type annotation"):

        class Model(BaseModel):
            a = Field('foobar')


def test_custom_init_subclass_params():
    class DerivedModel(BaseModel):
        def __init_subclass__(cls, something):
            cls.something = something

    # if this raises a TypeError, then there is a regression of issue 867:
    # pydantic.main.MetaModel.__new__ should include **kwargs at the end of the
    # method definition and pass them on to the super call at the end in order
    # to allow the special method __init_subclass__ to be defined with custom
    # parameters on extended BaseModel classes.
    class NewModel(DerivedModel, something=2):
        something: ClassVar = 1

    assert NewModel.something == 2


def test_recursive_model():
    class MyModel(BaseModel):
        field: Optional['MyModel']

    m = MyModel(field={'field': {'field': None}})
    assert m.model_dump() == {'field': {'field': {'field': None}}}


def test_recursive_cycle_with_repeated_field():
    class A(BaseModel):
        b: 'B'

    class B(BaseModel):
        a1: Optional[A] = None
        a2: Optional[A] = None

    A.model_rebuild()

    assert A.model_validate({'b': {'a1': {'b': {'a1': None}}}}) == A(b=B(a1=A(b=B(a1=None))))
    with pytest.raises(ValidationError) as exc_info:
        A.model_validate({'b': {'a1': {'a1': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'a1': None}, 'loc': ('b', 'a1', 'b'), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_two_defaults():
    with pytest.raises(TypeError, match='^cannot specify both default and default_factory$'):

        class Model(BaseModel):
            a: int = Field(default=3, default_factory=lambda: 3)


def test_default_factory():
    class ValueModel(BaseModel):
        uid: UUID = uuid4()

    m1 = ValueModel()
    m2 = ValueModel()
    assert m1.uid == m2.uid

    class DynamicValueModel(BaseModel):
        uid: UUID = Field(default_factory=uuid4)

    m1 = DynamicValueModel()
    m2 = DynamicValueModel()
    assert isinstance(m1.uid, UUID)
    assert m1.uid != m2.uid

    # With a callable: we still should be able to set callables as defaults
    class FunctionModel(BaseModel):
        a: int = 1
        uid: Callable[[], UUID] = Field(uuid4)

    m = FunctionModel()
    assert m.uid is uuid4

    # Returning a singleton from a default_factory is supported
    class MySingleton:
        pass

    MY_SINGLETON = MySingleton()

    class SingletonFieldModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        singleton: MySingleton = Field(default_factory=lambda: MY_SINGLETON)

    assert SingletonFieldModel().singleton is SingletonFieldModel().singleton


def test_default_factory_called_once():
    """It should call only once the given factory by default"""

    class Seq:
        def __init__(self):
            self.v = 0

        def __call__(self):
            self.v += 1
            return self.v

    class MyModel(BaseModel):
        id: int = Field(default_factory=Seq())

    m1 = MyModel()
    assert m1.id == 1
    m2 = MyModel()
    assert m2.id == 2
    assert m1.id == 1


def test_default_factory_called_once_2():
    """It should call only once the given factory by default"""

    v = 0

    def factory():
        nonlocal v
        v += 1
        return v

    class MyModel(BaseModel):
        id: int = Field(default_factory=factory)

    m1 = MyModel()
    assert m1.id == 1
    m2 = MyModel()
    assert m2.id == 2


def test_default_factory_validate_children():
    class Child(BaseModel):
        x: int

    class Parent(BaseModel):
        children: List[Child] = Field(default_factory=list)

    Parent(children=[{'x': 1}, {'x': 2}])
    with pytest.raises(ValidationError) as exc_info:
        Parent(children=[{'x': 1}, {'y': 2}])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('children', 1, 'x'), 'msg': 'Field required', 'input': {'y': 2}}
    ]


def test_default_factory_parse():
    class Inner(BaseModel):
        val: int = Field(0)

    class Outer(BaseModel):
        inner_1: Inner = Field(default_factory=Inner)
        inner_2: Inner = Field(Inner())

    default = Outer().model_dump()
    parsed = Outer.model_validate(default)
    assert parsed.model_dump() == {'inner_1': {'val': 0}, 'inner_2': {'val': 0}}
    assert repr(parsed) == 'Outer(inner_1=Inner(val=0), inner_2=Inner(val=0))'


def test_reuse_same_field():
    required_field = Field(...)

    class Model1(BaseModel):
        required: str = required_field

    class Model2(BaseModel):
        required: str = required_field

    with pytest.raises(ValidationError):
        Model1.model_validate({})
    with pytest.raises(ValidationError):
        Model2.model_validate({})


def test_base_config_type_hinting():
    class M(BaseModel):
        a: int

    get_type_hints(type(M.model_config))


def test_frozen_field():
    """assigning a frozen=True field should raise a TypeError"""

    class Entry(BaseModel):
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
    class Model(BaseModel):
        a: int = Field()
        b: float = Field(repr=True)
        c: bool = Field(repr=False)

    m = Model(a=1, b=2.5, c=True)
    assert repr(m) == 'Model(a=1, b=2.5)'
    assert repr(m.model_fields['a']) == 'FieldInfo(annotation=int, required=True)'
    assert repr(m.model_fields['b']) == 'FieldInfo(annotation=float, required=True)'
    assert repr(m.model_fields['c']) == 'FieldInfo(annotation=bool, required=True, repr=False)'


def test_inherited_model_field_copy():
    """It should copy models used as fields by default"""

    class Image(BaseModel):
        path: str

        def __hash__(self):
            return id(self)

    class Item(BaseModel):
        images: Set[Image]

    image_1 = Image(path='my_image1.png')
    image_2 = Image(path='my_image2.png')

    item = Item(images={image_1, image_2})
    assert image_1 in item.images

    assert id(image_1) in {id(image) for image in item.images}
    assert id(image_2) in {id(image) for image in item.images}


def test_mapping_subclass_as_input():
    class CustomMap(dict):
        pass

    class Model(BaseModel):
        x: Mapping[str, int]

    d = CustomMap()
    d['one'] = 1
    d['two'] = 2

    v = Model(x=d).x
    # we don't promise that this will or will not be a CustomMap
    # all we promise is that it _will_ be a mapping
    assert isinstance(v, Mapping)
    # but the current behavior is that it will be a dict, not a CustomMap
    # so document that here
    assert not isinstance(v, CustomMap)
    assert v == {'one': 1, 'two': 2}


def test_typing_coercion_dict():
    class Model(BaseModel):
        x: Dict[str, int]

    m = Model(x={'one': 1, 'two': 2})
    assert repr(m) == "Model(x={'one': 1, 'two': 2})"


KT = TypeVar('KT')
VT = TypeVar('VT')


class MyDict(Dict[KT, VT]):
    def __repr__(self):
        return f'MyDict({super().__repr__()})'


def test_class_kwargs_config():
    class Base(BaseModel, extra='forbid', alias_generator=str.upper):
        a: int

    assert Base.model_config['extra'] == 'forbid'
    assert Base.model_config['alias_generator'] is str.upper
    # assert Base.model_fields['a'].alias == 'A'

    class Model(Base, extra='allow'):
        b: int

    assert Model.model_config['extra'] == 'allow'  # overwritten as intended
    assert Model.model_config['alias_generator'] is str.upper  # inherited as intended
    # assert Model.model_fields['b'].alias == 'B'  # alias_generator still works


def test_class_kwargs_config_and_attr_conflict():
    class Model(BaseModel, extra='allow', alias_generator=str.upper):
        model_config = ConfigDict(extra='forbid', title='Foobar')
        b: int

    assert Model.model_config['extra'] == 'allow'
    assert Model.model_config['alias_generator'] is str.upper
    assert Model.model_config['title'] == 'Foobar'


def test_class_kwargs_custom_config():
    if platform.python_implementation() == 'PyPy':
        msg = r"__init_subclass__\(\) got an unexpected keyword argument 'some_config'"
    else:
        msg = r'__init_subclass__\(\) takes no keyword arguments'
    with pytest.raises(TypeError, match=msg):

        class Model(BaseModel, some_config='new_value'):
            a: int


@pytest.mark.skipif(sys.version_info < (3, 10), reason='need 3.10 version')
def test_new_union_origin():
    """On 3.10+, origin of `int | str` is `types.UnionType`, not `typing.Union`"""

    class Model(BaseModel):
        x: int | str

    assert Model(x=3).x == 3
    assert Model(x='3').x == '3'
    assert Model(x='pika').x == 'pika'
    # assert Model.model_json_schema() == {
    #     'title': 'Model',
    #     'type': 'object',
    #     'properties': {'x': {'title': 'X', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
    #     'required': ['x'],
    # }


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
@pytest.mark.parametrize(
    'value',
    [None, Field(...)],
    ids=['none', 'field'],
)
def test_final_field_decl_without_default_val(ann, value):
    class Model(BaseModel):
        a: ann

        if value is not None:
            a = value

    assert 'a' not in Model.__class_vars__
    assert 'a' in Model.model_fields

    assert Model.model_fields['a'].final


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
def test_final_field_decl_with_default_val(ann):
    class Model(BaseModel):
        a: ann = 10

    assert 'a' in Model.__class_vars__
    assert 'a' not in Model.model_fields


def test_final_field_reassignment():
    class Model(BaseModel):
        model_config = ConfigDict(validate_assignment=True)

        a: Final[int]

    obj = Model(a=10)

    with pytest.raises(ValidationError) as exc_info:
        obj.a = 20
    assert exc_info.value.errors(include_url=False) == [
        {'input': 20, 'loc': ('a',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]


def test_field_by_default_is_not_final():
    class Model(BaseModel):
        a: int

    assert not Model.model_fields['a'].final


def test_annotated_final():
    class Model(BaseModel):
        a: Annotated[Final[int], Field(title='abc')]

    assert Model.model_fields['a'].final
    assert Model.model_fields['a'].title == 'abc'

    class Model2(BaseModel):
        a: Final[Annotated[int, Field(title='def')]]

    assert Model2.model_fields['a'].final
    assert Model2.model_fields['a'].title == 'def'


def test_post_init():
    calls = []

    class InnerModel(BaseModel):
        a: int
        b: int

        def model_post_init(self, __context) -> None:
            super().model_post_init(__context)  # this is included just to show it doesn't error
            assert self.model_dump() == {'a': 3, 'b': 4}
            calls.append('inner_model_post_init')

    class Model(BaseModel):
        c: int
        d: int
        sub: InnerModel

        def model_post_init(self, __context) -> None:
            assert self.model_dump() == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}
            calls.append('model_post_init')

    m = Model(c=1, d='2', sub={'a': 3, 'b': '4'})
    assert calls == ['inner_model_post_init', 'model_post_init']
    assert m.model_dump() == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}

    class SubModel(Model):
        def model_post_init(self, __context) -> None:
            assert self.model_dump() == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}
            super().model_post_init(__context)
            calls.append('submodel_post_init')

    calls.clear()
    m = SubModel(c=1, d='2', sub={'a': 3, 'b': '4'})
    assert calls == ['inner_model_post_init', 'model_post_init', 'submodel_post_init']
    assert m.model_dump() == {'c': 1, 'd': 2, 'sub': {'a': 3, 'b': 4}}


@pytest.mark.parametrize('include_private_attribute', [True, False])
def test_post_init_call_signatures(include_private_attribute):
    calls = []

    class Model(BaseModel):
        a: int
        b: int
        if include_private_attribute:
            _x: int = PrivateAttr(1)

        def model_post_init(self, *args, **kwargs) -> None:
            calls.append((args, kwargs))

    Model(a=1, b=2)
    assert calls == [((None,), {})]
    Model.model_construct(a=3, b=4)
    assert calls == [((None,), {}), ((None,), {})]


def test_post_init_not_called_without_override():
    calls = []

    def monkey_patched_model_post_init(cls, __context):
        calls.append('BaseModel.model_post_init')

    original_base_model_post_init = BaseModel.model_post_init
    try:
        BaseModel.model_post_init = monkey_patched_model_post_init

        class WithoutOverrideModel(BaseModel):
            pass

        WithoutOverrideModel()
        WithoutOverrideModel.model_construct()
        assert calls == []

        class WithOverrideModel(BaseModel):
            def model_post_init(self, __context: Any) -> None:
                calls.append('WithOverrideModel.model_post_init')

        WithOverrideModel()
        assert calls == ['WithOverrideModel.model_post_init']
        WithOverrideModel.model_construct()
        assert calls == ['WithOverrideModel.model_post_init', 'WithOverrideModel.model_post_init']

    finally:
        BaseModel.model_post_init = original_base_model_post_init


def test_deeper_recursive_model():
    class A(BaseModel):
        b: 'B'

    class B(BaseModel):
        c: 'C'

    class C(BaseModel):
        a: Optional['A']

    A.model_rebuild()
    B.model_rebuild()
    C.model_rebuild()

    m = A(b=B(c=C(a=None)))
    assert m.model_dump() == {'b': {'c': {'a': None}}}


def test_model_rebuild_localns():
    class A(BaseModel):
        x: int

    class B(BaseModel):
        a: 'Model'  # noqa: F821

    B.model_rebuild(_types_namespace={'Model': A})

    m = B(a={'x': 1})
    assert m.model_dump() == {'a': {'x': 1}}
    assert isinstance(m.a, A)

    class C(BaseModel):
        a: 'Model'  # noqa: F821

    with pytest.raises(PydanticUndefinedAnnotation, match="name 'Model' is not defined"):
        C.model_rebuild(_types_namespace={'A': A})


def test_model_rebuild_zero_depth():
    class Model(BaseModel):
        x: 'X_Type'

    X_Type = str

    with pytest.raises(NameError, match='X_Type'):
        Model.model_rebuild(_parent_namespace_depth=0)

    Model.__pydantic_parent_namespace__.update({'X_Type': int})
    Model.model_rebuild(_parent_namespace_depth=0)

    m = Model(x=42)
    assert m.model_dump() == {'x': 42}


@pytest.fixture(scope='session', name='InnerEqualityModel')
def inner_equality_fixture():
    class InnerEqualityModel(BaseModel):
        iw: int
        ix: int = 0
        _iy: int = PrivateAttr()
        _iz: int = PrivateAttr(0)

    return InnerEqualityModel


@pytest.fixture(scope='session', name='EqualityModel')
def equality_fixture(InnerEqualityModel):
    class EqualityModel(BaseModel):
        w: int
        x: int = 0
        _y: int = PrivateAttr()
        _z: int = PrivateAttr(0)

        model: InnerEqualityModel

    return EqualityModel


def test_model_equality(EqualityModel, InnerEqualityModel):
    m1 = EqualityModel(w=0, x=0, model=InnerEqualityModel(iw=0))
    m2 = EqualityModel(w=0, x=0, model=InnerEqualityModel(iw=0))
    assert m1 == m2


def test_model_equality_type(EqualityModel, InnerEqualityModel):
    class Model1(BaseModel):
        x: int

    class Model2(BaseModel):
        x: int

    m1 = Model1(x=1)
    m2 = Model2(x=1)

    assert m1.model_dump() == m2.model_dump()
    assert m1 != m2


def test_model_equality_dump(EqualityModel, InnerEqualityModel):
    inner_model = InnerEqualityModel(iw=0)
    assert inner_model != inner_model.model_dump()

    model = EqualityModel(w=0, x=0, model=inner_model)
    assert model != dict(model)
    assert dict(model) != model.model_dump()  # Due to presence of inner model


def test_model_equality_fields_set(InnerEqualityModel):
    m1 = InnerEqualityModel(iw=0)
    m2 = InnerEqualityModel(iw=0, ix=0)
    assert m1.model_fields_set != m2.model_fields_set
    assert m1 == m2


def test_model_equality_private_attrs(InnerEqualityModel):
    m = InnerEqualityModel(iw=0, ix=0)

    m1 = m.model_copy()
    m2 = m.model_copy()
    m3 = m.model_copy()

    m2._iy = 1
    m3._iz = 1

    models = [m1, m2, m3]
    for i, first_model in enumerate(models):
        for j, second_model in enumerate(models):
            if i == j:
                assert first_model == second_model
            else:
                assert first_model != second_model

    m2_equal = m.model_copy()
    m2_equal._iy = 1
    assert m2 == m2_equal

    m3_equal = m.model_copy()
    m3_equal._iz = 1
    assert m3 == m3_equal


def test_model_copy_extra():
    class Model(BaseModel, extra='allow'):
        x: int

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 1, 'y': 2}
    assert m.model_extra == {'y': 2}
    m2 = m.model_copy()
    assert m2.model_dump() == {'x': 1, 'y': 2}
    assert m2.model_extra == {'y': 2}

    m3 = m.model_copy(update={'x': 4, 'z': 3})
    assert m3.model_dump() == {'x': 4, 'y': 2, 'z': 3}
    assert m3.model_extra == {'y': 2, 'z': 3}

    m4 = m.model_copy(update={'x': 4, 'z': 3})
    assert m4.model_dump() == {'x': 4, 'y': 2, 'z': 3}
    assert m4.model_extra == {'y': 2, 'z': 3}

    m = Model(x=1, a=2)
    m.__pydantic_extra__ = None
    m5 = m.model_copy(update={'x': 4, 'b': 3})
    assert m5.model_dump() == {'x': 4, 'b': 3}
    assert m5.model_extra == {'b': 3}


def test_model_parametrized_name_not_generic():
    class Model(BaseModel):
        x: int

    with pytest.raises(TypeError, match='Concrete names should only be generated for generic models.'):
        Model.model_parametrized_name(())


def test_model_equality_generics():
    T = TypeVar('T')

    class GenericModel(BaseModel, Generic[T]):
        x: T

    class ConcreteModel(BaseModel):
        x: int

    assert ConcreteModel(x=1) != GenericModel(x=1)
    assert ConcreteModel(x=1) != GenericModel[Any](x=1)
    assert ConcreteModel(x=1) != GenericModel[int](x=1)

    assert GenericModel(x=1) != GenericModel(x=2)

    S = TypeVar('S')
    assert GenericModel(x=1) == GenericModel(x=1)
    assert GenericModel(x=1) == GenericModel[S](x=1)
    assert GenericModel(x=1) == GenericModel[Any](x=1)
    assert GenericModel(x=1) == GenericModel[float](x=1)

    assert GenericModel[int](x=1) == GenericModel[int](x=1)
    assert GenericModel[int](x=1) == GenericModel[S](x=1)
    assert GenericModel[int](x=1) == GenericModel[Any](x=1)
    assert GenericModel[int](x=1) == GenericModel[float](x=1)

    # Test that it works with nesting as well
    nested_any = GenericModel[GenericModel[Any]](x=GenericModel[Any](x=1))
    nested_int = GenericModel[GenericModel[int]](x=GenericModel[int](x=1))
    assert nested_any == nested_int


def test_model_validate_strict() -> None:
    class LaxModel(BaseModel):
        x: int

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        x: int

        model_config = ConfigDict(strict=True)

    assert LaxModel.model_validate({'x': '1'}, strict=None) == LaxModel(x=1)
    assert LaxModel.model_validate({'x': '1'}, strict=False) == LaxModel(x=1)
    with pytest.raises(ValidationError) as exc_info:
        LaxModel.model_validate({'x': '1'}, strict=True)
    # there's no such thing on the model itself
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        StrictModel.model_validate({'x': '1'})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert StrictModel.model_validate({'x': '1'}, strict=False) == StrictModel(x=1)
    with pytest.raises(ValidationError) as exc_info:
        LaxModel.model_validate({'x': '1'}, strict=True)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_model_validate_json_strict() -> None:
    class LaxModel(BaseModel):
        x: int

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        x: int

        model_config = ConfigDict(strict=True)

    assert LaxModel.model_validate_json(json.dumps({'x': '1'}), strict=None) == LaxModel(x=1)
    assert LaxModel.model_validate_json(json.dumps({'x': '1'}), strict=False) == LaxModel(x=1)
    with pytest.raises(ValidationError) as exc_info:
        LaxModel.model_validate_json(json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        StrictModel.model_validate_json(json.dumps({'x': '1'}), strict=None)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert StrictModel.model_validate_json(json.dumps({'x': '1'}), strict=False) == StrictModel(x=1)
    with pytest.raises(ValidationError) as exc_info:
        StrictModel.model_validate_json(json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_validate_python_context() -> None:
    contexts: List[Any] = [None, None, {'foo': 'bar'}]

    class Model(BaseModel):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    Model.model_validate({'x': 1})
    Model.model_validate({'x': 1}, context=None)
    Model.model_validate({'x': 1}, context={'foo': 'bar'})
    assert contexts == []


def test_validate_json_context() -> None:
    contexts: List[Any] = [None, None, {'foo': 'bar'}]

    class Model(BaseModel):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    Model.model_validate_json(json.dumps({'x': 1}))
    Model.model_validate_json(json.dumps({'x': 1}), context=None)
    Model.model_validate_json(json.dumps({'x': 1}), context={'foo': 'bar'})
    assert contexts == []


def test_pydantic_init_subclass() -> None:
    calls = []

    class MyModel(BaseModel):
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__()  # can't pass kwargs to object.__init_subclass__, weirdly
            calls.append((cls.__name__, '__init_subclass__', kwargs))

        @classmethod
        def __pydantic_init_subclass__(cls, **kwargs):
            super().__pydantic_init_subclass__(**kwargs)
            calls.append((cls.__name__, '__pydantic_init_subclass__', kwargs))

    class MySubModel(MyModel, a=1):
        pass

    assert calls == [
        ('MySubModel', '__init_subclass__', {'a': 1}),
        ('MySubModel', '__pydantic_init_subclass__', {'a': 1}),
    ]


def test_model_validate_with_context():
    class InnerModel(BaseModel):
        x: int

        @field_validator('x')
        def validate(cls, value, info):
            return value * info.context.get('multiplier', 1)

    class OuterModel(BaseModel):
        inner: InnerModel

    assert OuterModel.model_validate({'inner': {'x': 2}}, context={'multiplier': 1}).inner.x == 2
    assert OuterModel.model_validate({'inner': {'x': 2}}, context={'multiplier': 2}).inner.x == 4
    assert OuterModel.model_validate({'inner': {'x': 2}}, context={'multiplier': 3}).inner.x == 6


def test_extra_equality():
    class MyModel(BaseModel, extra='allow'):
        pass

    assert MyModel(x=1) != MyModel()


def test_equality_delegation():
    from unittest.mock import ANY

    class MyModel(BaseModel):
        foo: str

    assert MyModel(foo='bar') == ANY


def test_recursion_loop_error():
    class Model(BaseModel):
        x: List['Model']

    data = {'x': []}
    data['x'].append(data)
    with pytest.raises(ValidationError) as exc_info:
        Model(**data)
    assert repr(exc_info.value.errors(include_url=False)[0]) == (
        "{'type': 'recursion_loop', 'loc': ('x', 0, 'x', 0), 'msg': "
        "'Recursion error - cyclic reference detected', 'input': {'x': [{...}]}}"
    )


def test_protected_namespace_default():
    with pytest.raises(NameError, match='Field "model_prefixed_field" has conflict with protected namespace "model_"'):

        class Model(BaseModel):
            model_prefixed_field: str


def test_custom_protected_namespace():
    with pytest.raises(NameError, match='Field "test_field" has conflict with protected namespace "test_"'):

        class Model(BaseModel):
            # this field won't raise error because we changed the default value for the
            # `protected_namespaces` config.
            model_prefixed_field: str
            test_field: str

            model_config = ConfigDict(protected_namespaces=('test_',))


def test_multiple_protected_namespace():
    with pytest.raises(
        NameError, match='Field "also_protect_field" has conflict with protected namespace "also_protect_"'
    ):

        class Model(BaseModel):
            also_protect_field: str

            model_config = ConfigDict(protected_namespaces=('protect_me_', 'also_protect_'))


def test_model_get_core_schema() -> None:
    class Model(BaseModel):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            assert handler(int) == {'type': 'int'}
            assert handler(int) == {'type': 'int'}
            return handler(source_type)

    Model()


def test_nested_types_ignored():
    from pydantic import BaseModel

    class NonNestedType:
        pass

    # Defining a nested type does not error
    class GoodModel(BaseModel):
        class NestedType:
            pass

        # You can still store such types on the class by annotating as a ClassVar
        MyType: ClassVar[Type[Any]] = NonNestedType

        # For documentation: you _can_ give multiple names to a nested type and it won't error:
        # It might be better if it did, but this seems to be rare enough that I'm not concerned
        x = NestedType

    assert GoodModel.MyType is NonNestedType
    assert GoodModel.x is GoodModel.NestedType

    with pytest.raises(PydanticUserError, match='A non-annotated attribute was detected'):

        class BadModel(BaseModel):
            x = NonNestedType


def test_validate_python_from_attributes() -> None:
    class Model(BaseModel):
        x: int

    class ModelFromAttributesTrue(Model):
        model_config = ConfigDict(from_attributes=True)

    class ModelFromAttributesFalse(Model):
        model_config = ConfigDict(from_attributes=False)

    @dataclass
    class UnrelatedClass:
        x: int = 1

    input = UnrelatedClass(1)

    for from_attributes in (False, None):
        with pytest.raises(ValidationError) as exc_info:
            Model.model_validate(UnrelatedClass(), from_attributes=from_attributes)
        assert exc_info.value.errors(include_url=False) == [
            {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': input}
        ]

    res = Model.model_validate(UnrelatedClass(), from_attributes=True)
    assert res == Model(x=1)

    with pytest.raises(ValidationError) as exc_info:
        ModelFromAttributesTrue.model_validate(UnrelatedClass(), from_attributes=False)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': input}
    ]

    for from_attributes in (True, None):
        res = ModelFromAttributesTrue.model_validate(UnrelatedClass(), from_attributes=from_attributes)
        assert res == ModelFromAttributesTrue(x=1)

    for from_attributes in (False, None):
        with pytest.raises(ValidationError) as exc_info:
            ModelFromAttributesFalse.model_validate(UnrelatedClass(), from_attributes=from_attributes)
        assert exc_info.value.errors(include_url=False) == [
            {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': input}
        ]

    res = ModelFromAttributesFalse.model_validate(UnrelatedClass(), from_attributes=True)
    assert res == ModelFromAttributesFalse(x=1)


def test_model_signature_annotated() -> None:
    class Model(BaseModel):
        x: Annotated[int, 123]

    # we used to accidentally convert `__metadata__` to a list
    # which caused things like `typing.get_args()` to fail
    assert Model.__signature__.parameters['x'].annotation.__metadata__ == (123,)


def test_get_core_schema_unpacks_refs_for_source_type() -> None:
    # use a list to track since we end up calling `__get_pydantic_core_schema__` multiple times for models
    # e.g. InnerModel.__get_pydantic_core_schema__ gets called:
    # 1. When InnerModel is defined
    # 2. When OuterModel is defined
    # 3. When we use the TypeAdapter
    received_schemas: dict[str, list[str]] = defaultdict(list)

    @dataclass
    class Marker:
        name: str

        def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas[self.name].append(schema['type'])
            return schema

    class InnerModel(BaseModel):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas['InnerModel'].append(schema['type'])
            schema['metadata'] = schema.get('metadata', {})
            schema['metadata']['foo'] = 'inner was here!'
            return deepcopy(schema)

    class OuterModel(BaseModel):
        inner: Annotated[InnerModel, Marker('Marker("inner")')]

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            received_schemas['OuterModel'].append(schema['type'])
            return schema

    ta = TypeAdapter(Annotated[OuterModel, Marker('Marker("outer")')])

    # super hacky check but it works in all cases and avoids a complex and fragile iteration over CoreSchema
    # the point here is to verify that `__get_pydantic_core_schema__`
    assert 'inner was here' in str(ta.core_schema)

    assert received_schemas == {
        'InnerModel': ['model', 'model', 'model'],
        'Marker("inner")': ['definition-ref', 'definition-ref'],
        'OuterModel': ['model', 'model'],
        'Marker("outer")': ['definition-ref'],
    }


def test_get_core_schema_return_new_ref() -> None:
    class InnerModel(BaseModel):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)
            schema = deepcopy(schema)
            schema['metadata'] = schema.get('metadata', {})
            schema['metadata']['foo'] = 'inner was here!'
            return deepcopy(schema)

    class OuterModel(BaseModel):
        inner: InnerModel
        x: int = 1

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            schema = handler(source_type)

            def set_x(m: 'OuterModel') -> 'OuterModel':
                m.x += 1
                return m

            return core_schema.no_info_after_validator_function(set_x, schema, ref=schema.pop('ref'))

    cs = OuterModel.__pydantic_core_schema__
    # super hacky check but it works in all cases and avoids a complex and fragile iteration over CoreSchema
    # the point here is to verify that `__get_pydantic_core_schema__`
    assert 'inner was here' in str(cs)

    assert OuterModel(inner=InnerModel()).x == 2
