import sys
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Counter,
    DefaultDict,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    get_type_hints,
)
from uuid import UUID, uuid4

import pytest
from typing_extensions import Annotated

from pydantic import (
    BaseConfig,
    BaseModel,
    ConfigError,
    Extra,
    Field,
    NoneBytes,
    NoneStr,
    PrivateAttr,
    Required,
    SecretStr,
    ValidationError,
    constr,
    root_validator,
    validator,
)
from pydantic.typing import Final, Literal


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


class UltraSimpleModel(BaseModel):
    a: float
    b: int = 10


def test_ultra_simple_missing():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert str(m) == 'a=10.2 b=10'
    assert repr(m) == 'UltraSimpleModel(a=10.2, b=10)'
    assert repr(m.__fields__['a']) == "ModelField(name='a', type=float, required=True)"
    assert repr(m.__fields__['b']) == "ModelField(name='b', type=int, required=False, default=10)"
    assert dict(m) == {'a': 10.2, 'b': 10}
    assert m.dict() == {'a': 10.2, 'b': 10}
    assert m.json() == '{"a": 10.2, "b": 10}'
    assert str(m) == 'a=10.2 b=10'


def test_default_factory_field():
    def myfunc():
        return 1

    class Model(BaseModel):
        a: int = Field(default_factory=myfunc)

    m = Model()
    assert str(m) == 'a=1'
    assert (
        repr(m.__fields__['a']) == "ModelField(name='a', type=int, required=False, default_factory='<function myfunc>')"
    )
    assert dict(m) == {'a': 1}
    assert m.json() == '{"a": 1}'


def test_default_factory_no_type_field():
    def myfunc():
        return 1

    with pytest.raises(ConfigError) as e:

        class Model(BaseModel):
            a = Field(default_factory=myfunc)

    assert str(e.value) == "you need to set the type of field 'a' when using `default_factory`"


def test_comparing():
    m = UltraSimpleModel(a=10.2, b='100')
    assert m == {'a': 10.2, 'b': 100}
    assert m == UltraSimpleModel(a=10.2, b=100)


def test_nullable_strings_success():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    m = NoneCheckModel(
        required_str_value='v1', required_str_none_value=None, required_bytes_value='v2', required_bytes_none_value=None
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    with pytest.raises(ValidationError) as exc_info:
        NoneCheckModel(
            required_str_value=None,
            required_str_none_value=None,
            required_bytes_value=None,
            required_bytes_none_value=None,
        )
    assert exc_info.value.errors() == [
        {'loc': ('required_str_value',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
        {
            'loc': ('required_bytes_value',),
            'msg': 'none is not an allowed value',
            'type': 'type_error.none.not_allowed',
        },
    ]


class RecursiveModel(BaseModel):
    grape: bool = ...
    banana: UltraSimpleModel = ...


def test_recursion():
    m = RecursiveModel(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == 'RecursiveModel(grape=True, banana=UltraSimpleModel(a=1.0, b=10))'


def test_recursion_fails():
    with pytest.raises(ValidationError):
        RecursiveModel(grape=1, banana=123)


def test_not_required():
    class Model(BaseModel):
        a: float = None

    assert Model(a=12.2).a == 12.2
    assert Model().a is None
    assert Model(a=None).a is None


def test_infer_type():
    class Model(BaseModel):
        a = False
        b = ''
        c = 0

    assert Model().a is False
    assert Model().b == ''
    assert Model().c == 0


def test_allow_extra():
    class Model(BaseModel):
        a: float = ...

        class Config:
            extra = Extra.allow

    assert Model(a='10.2', b=12).dict() == {'a': 10.2, 'b': 12}


def test_allow_extra_repr():
    class Model(BaseModel):
        a: float = ...

        class Config:
            extra = Extra.allow

    assert str(Model(a='10.2', b=12)) == 'a=10.2 b=12'


def test_forbidden_extra_success():
    class ForbiddenExtra(BaseModel):
        foo = 'whatever'

        class Config:
            extra = Extra.forbid

    m = ForbiddenExtra()
    assert m.foo == 'whatever'

    m = ForbiddenExtra(foo=1)
    assert m.foo == '1'


def test_forbidden_extra_fails():
    class ForbiddenExtra(BaseModel):
        foo = 'whatever'

        class Config:
            extra = Extra.forbid

    with pytest.raises(ValidationError) as exc_info:
        ForbiddenExtra(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.errors() == [
        {'loc': ('bar',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
        {'loc': ('spam',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_disallow_mutation():
    class Model(BaseModel):
        a: float

    model = Model(a=0.2)
    with pytest.raises(ValueError, match='"Model" object has no field "b"'):
        model.b = 2


def test_extra_allowed():
    class Model(BaseModel):
        a: float

        class Config:
            extra = Extra.allow

    model = Model(a=0.2, b=0.1)
    assert model.b == 0.1

    assert not hasattr(model, 'c')
    model.c = 1
    assert hasattr(model, 'c')
    assert model.c == 1


def test_extra_ignored():
    class Model(BaseModel):
        a: float

        class Config:
            extra = Extra.ignore

    model = Model(a=0.2, b=0.1)
    assert not hasattr(model, 'b')

    with pytest.raises(ValueError, match='"Model" object has no field "c"'):
        model.c = 1


def test_set_attr():
    m = UltraSimpleModel(a=10.2)
    assert m.dict() == {'a': 10.2, 'b': 10}

    m.b = 20
    assert m.dict() == {'a': 10.2, 'b': 20}


def test_set_attr_invalid():
    class UltraSimpleModel(BaseModel):
        a: float = ...
        b: int = 10

    m = UltraSimpleModel(a=10.2)
    assert m.dict() == {'a': 10.2, 'b': 10}

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


def test_alias():
    class SubModel(BaseModel):
        c = 'barfoo'

        class Config:
            fields = {'c': {'alias': '_c'}}

    class Model(BaseModel):
        a = 'foobar'
        b: SubModel = SubModel()

        class Config:
            fields = {'a': {'alias': '_a'}}

    assert Model().a == 'foobar'
    assert Model().b.c == 'barfoo'
    assert Model().dict() == {'a': 'foobar', 'b': {'c': 'barfoo'}}
    assert Model(_a='different').a == 'different'
    assert Model(b={'_c': 'different'}).b.c == 'different'
    assert Model(_a='different', b={'_c': 'different'}).dict() == {'a': 'different', 'b': {'c': 'different'}}
    assert Model(_a='different', b={'_c': 'different'}).dict(by_alias=True) == {
        '_a': 'different',
        'b': {'_c': 'different'},
    }


def test_population_by_field_name():
    class Model(BaseModel):
        a: str

        class Config:
            allow_population_by_field_name = True
            fields = {'a': {'alias': '_a'}}

    assert Model(a='different').a == 'different'
    assert Model(a='different').dict() == {'a': 'different'}
    assert Model(a='different').dict(by_alias=True) == {'_a': 'different'}


def test_field_order():
    class Model(BaseModel):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    assert list(Model.__fields__.keys()) == ['c', 'b', 'a', 'd']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float = Required
        b: int = 10

    m = Model(a=10.2)
    assert m.dict() == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_mutability():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = True
            extra = Extra.forbid
            frozen = False

    m = TestModel()

    assert m.a == 10
    m.a = 11
    assert m.a == 11


@pytest.mark.parametrize('allow_mutation_, frozen_', [(False, False), (False, True), (True, True)])
def test_immutability(allow_mutation_, frozen_):
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = allow_mutation_
            extra = Extra.forbid
            frozen = frozen_

    m = TestModel()

    assert m.a == 10
    with pytest.raises(TypeError) as exc_info:
        m.a = 11
    assert '"TestModel" is immutable and does not support item assignment' in exc_info.value.args[0]


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
        a: int = 10

        class Config:
            frozen = True

    m = TestModel()
    assert m.__hash__ is not None
    assert isinstance(hash(m), int)


def test_frozen_with_unhashable_fields_are_not_hashable():
    class TestModel(BaseModel):
        a: int = 10
        y: List[int] = [1, 2, 3]

        class Config:
            frozen = True

    m = TestModel()
    with pytest.raises(TypeError) as exc_info:
        hash(m)
    assert "unhashable type: 'list'" in exc_info.value.args[0]


def test_hash_function_give_different_result_for_different_object():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            frozen = True

    m = TestModel()
    m2 = TestModel()
    m3 = TestModel(a=11)
    assert hash(m) == hash(m2)
    assert hash(m) != hash(m3)

    # Redefined `TestModel`
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            frozen = True

    m4 = TestModel()
    assert hash(m) != hash(m4)


def test_const_validates():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    m = Model(a=3)
    assert m.a == 3


def test_const_uses_default():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    m = Model()
    assert m.a == 3


def test_const_validates_after_type_validators():
    # issue #1410
    class Model(BaseModel):
        a: int = Field(3, const=True)

    m = Model(a='3')
    assert m.a == 3


def test_const_with_wrong_value():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=4)

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'unexpected value; permitted: 3',
            'type': 'value_error.const',
            'ctx': {'given': 4, 'permitted': [3]},
        }
    ]


def test_const_with_validator():
    class Model(BaseModel):
        a: int = Field(3, const=True)

        @validator('a')
        def validate(v):
            return v

    with pytest.raises(ValidationError) as exc_info:
        Model(a=4)

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'unexpected value; permitted: 3',
            'type': 'value_error.const',
            'ctx': {'given': 4, 'permitted': [3]},
        }
    ]


def test_const_list():
    class SubModel(BaseModel):
        b: int

    class Model(BaseModel):
        a: List[SubModel] = Field([SubModel(b=1), SubModel(b=2), SubModel(b=3)], const=True)
        b: List[SubModel] = Field([{'b': 4}, {'b': 5}, {'b': 6}], const=True)

    m = Model()
    assert m.a == [SubModel(b=1), SubModel(b=2), SubModel(b=3)]
    assert m.b == [SubModel(b=4), SubModel(b=5), SubModel(b=6)]
    assert m.schema() == {
        'definitions': {
            'SubModel': {
                'properties': {'b': {'title': 'B', 'type': 'integer'}},
                'required': ['b'],
                'title': 'SubModel',
                'type': 'object',
            }
        },
        'properties': {
            'a': {
                'const': [SubModel(b=1), SubModel(b=2), SubModel(b=3)],
                'default': [{'b': 1}, {'b': 2}, {'b': 3}],
                'items': {'$ref': '#/definitions/SubModel'},
                'title': 'A',
                'type': 'array',
            },
            'b': {
                'const': [{'b': 4}, {'b': 5}, {'b': 6}],
                'default': [{'b': 4}, {'b': 5}, {'b': 6}],
                'items': {'$ref': '#/definitions/SubModel'},
                'title': 'B',
                'type': 'array',
            },
        },
        'title': 'Model',
        'type': 'object',
    }


def test_const_list_with_wrong_value():
    class SubModel(BaseModel):
        b: int

    class Model(BaseModel):
        a: List[SubModel] = Field([SubModel(b=1), SubModel(b=2), SubModel(b=3)], const=True)
        b: List[SubModel] = Field([{'b': 4}, {'b': 5}, {'b': 6}], const=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=[{'b': 3}, {'b': 1}, {'b': 2}], b=[{'b': 6}, {'b': 5}])

    assert exc_info.value.errors() == [
        {
            'ctx': {
                'given': [{'b': 3}, {'b': 1}, {'b': 2}],
                'permitted': [[SubModel(b=1), SubModel(b=2), SubModel(b=3)]],
            },
            'loc': ('a',),
            'msg': 'unexpected value; permitted: [SubModel(b=1), SubModel(b=2), SubModel(b=3)]',
            'type': 'value_error.const',
        },
        {
            'ctx': {'given': [{'b': 6}, {'b': 5}], 'permitted': [[{'b': 4}, {'b': 5}, {'b': 6}]]},
            'loc': ('b',),
            'msg': "unexpected value; permitted: [{'b': 4}, {'b': 5}, {'b': 6}]",
            'type': 'value_error.const',
        },
    ]
    assert exc_info.value.json().startswith('[')

    with pytest.raises(ValidationError) as exc_info:
        Model(a=[SubModel(b=3), SubModel(b=1), SubModel(b=2)], b=[SubModel(b=3), SubModel(b=1)])

    assert exc_info.value.errors() == [
        {
            'ctx': {
                'given': [SubModel(b=3), SubModel(b=1), SubModel(b=2)],
                'permitted': [[SubModel(b=1), SubModel(b=2), SubModel(b=3)]],
            },
            'loc': ('a',),
            'msg': 'unexpected value; permitted: [SubModel(b=1), SubModel(b=2), SubModel(b=3)]',
            'type': 'value_error.const',
        },
        {
            'ctx': {'given': [SubModel(b=3), SubModel(b=1)], 'permitted': [[{'b': 4}, {'b': 5}, {'b': 6}]]},
            'loc': ('b',),
            'msg': "unexpected value; permitted: [{'b': 4}, {'b': 5}, {'b': 6}]",
            'type': 'value_error.const',
        },
    ]
    assert exc_info.value.json().startswith('[')


def test_const_validation_json_serializable():
    class SubForm(BaseModel):
        field: int

    class Form(BaseModel):
        field1: SubForm = Field({'field': 2}, const=True)
        field2: List[SubForm] = Field([{'field': 2}], const=True)

    with pytest.raises(ValidationError) as exc_info:
        # Fails
        Form(field1={'field': 1}, field2=[{'field': 1}])

    # This should not raise an Json error
    exc_info.value.json()


class ValidateAssignmentModel(BaseModel):
    a: int = 2
    b: constr(min_length=1)

    class Config:
        validate_assignment = True


def test_validating_assignment_pass():
    p = ValidateAssignmentModel(a=5, b='hello')
    p.a = 2
    assert p.a == 2
    assert p.dict() == {'a': 2, 'b': 'hello'}
    p.b = 'hi'
    assert p.b == 'hi'
    assert p.dict() == {'a': 2, 'b': 'hi'}


def test_validating_assignment_fail():
    p = ValidateAssignmentModel(a=5, b='hello')

    with pytest.raises(ValidationError) as exc_info:
        p.a = 'b'
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        p.b = ''
    assert exc_info.value.errors() == [
        {
            'loc': ('b',),
            'msg': 'ensure this value has at least 1 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 1},
        }
    ]


def test_validating_assignment_pre_root_validator_fail():
    class Model(BaseModel):
        current_value: float = Field(..., alias='current')
        max_value: float

        class Config:
            validate_assignment = True

        @root_validator(pre=True)
        def values_are_not_string(cls, values):
            if any(isinstance(x, str) for x in values.values()):
                raise ValueError('values cannot be a string')
            return values

    m = Model(current=100, max_value=200)
    with pytest.raises(ValidationError) as exc_info:
        m.current_value = '100'
    assert exc_info.value.errors() == [
        {
            'loc': ('__root__',),
            'msg': 'values cannot be a string',
            'type': 'value_error',
        }
    ]


def test_validating_assignment_post_root_validator_fail():
    class Model(BaseModel):
        current_value: float = Field(..., alias='current')
        max_value: float

        class Config:
            validate_assignment = True

        @root_validator
        def current_lessequal_max(cls, values):
            current_value = values.get('current_value')
            max_value = values.get('max_value')
            if current_value > max_value:
                raise ValueError('current_value cannot be greater than max_value')
            return values

        @root_validator(skip_on_failure=True)
        def current_lessequal_300(cls, values):
            current_value = values.get('current_value')
            if current_value > 300:
                raise ValueError('current_value cannot be greater than 300')
            return values

        @root_validator
        def current_lessequal_500(cls, values):
            current_value = values.get('current_value')
            if current_value > 500:
                raise ValueError('current_value cannot be greater than 500')
            return values

    m = Model(current=100, max_value=200)
    m.current_value = '100'
    with pytest.raises(ValidationError) as exc_info:
        m.current_value = 1000
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'current_value cannot be greater than max_value', 'type': 'value_error'},
        {
            'loc': ('__root__',),
            'msg': 'current_value cannot be greater than 500',
            'type': 'value_error',
        },
    ]


def test_root_validator_many_values_change():
    """It should run root_validator on assignment and update ALL concerned fields"""

    class Rectangle(BaseModel):
        width: float
        height: float
        area: float = None

        class Config:
            validate_assignment = True

        @root_validator
        def set_area(cls, values):
            values['area'] = values['width'] * values['height']
            return values

    r = Rectangle(width=1, height=1)
    assert r.area == 1
    r.height = 5
    assert r.area == 5


def test_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Model(BaseModel):
        foo: FooEnum = None

        class Config:
            use_enum_values = True

    m = Model(foo='foo')
    # this is the actual value, so has not "values" field
    assert not isinstance(m.foo, FooEnum)
    assert m.foo == 'foo'


def test_literal_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo_value', 'bar': 'bar_value'})

    class Model(BaseModel):
        baz: Literal[FooEnum.foo]
        boo: str = 'hoo'

        class Config:
            use_enum_values = True

    m = Model(baz=FooEnum.foo)
    assert m.dict() == {'baz': 'foo_value', 'boo': 'hoo'}
    assert m.baz.value == 'foo_value'

    with pytest.raises(ValidationError) as exc_info:
        Model(baz=FooEnum.bar)

    assert exc_info.value.errors() == [
        {
            'loc': ('baz',),
            'msg': "unexpected value; permitted: <FooEnum.foo: 'foo_value'>",
            'type': 'value_error.const',
            'ctx': {'given': FooEnum.bar, 'permitted': (FooEnum.foo,)},
        },
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
    assert m.dict() == {'foo': {'a', 'b'}, 'bar': ('c', 'd')}


def test_default_copy():
    class User(BaseModel):
        friends: List[int] = []

    u1 = User()
    u2 = User()
    assert u1.friends is not u2.friends


class ArbitraryType:
    pass


def test_arbitrary_type_allowed_validation_success():
    class ArbitraryTypeAllowedModel(BaseModel):
        t: ArbitraryType

        class Config:
            arbitrary_types_allowed = True

    arbitrary_type_instance = ArbitraryType()
    m = ArbitraryTypeAllowedModel(t=arbitrary_type_instance)
    assert m.t == arbitrary_type_instance


def test_arbitrary_type_allowed_validation_fails():
    class ArbitraryTypeAllowedModel(BaseModel):
        t: ArbitraryType

        class Config:
            arbitrary_types_allowed = True

    class C:
        pass

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryTypeAllowedModel(t=C())
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'instance of ArbitraryType expected',
            'type': 'type_error.arbitrary_type',
            'ctx': {'expected_arbitrary_type': 'ArbitraryType'},
        }
    ]


def test_arbitrary_types_not_allowed():
    with pytest.raises(RuntimeError) as exc_info:

        class ArbitraryTypeNotAllowedModel(BaseModel):
            t: ArbitraryType

    assert exc_info.value.args[0].startswith('no validator found for')


def test_type_type_validation_success():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    arbitrary_type_class = ArbitraryType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_subclass_validation_success():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    class ArbitrarySubType(ArbitraryType):
        pass

    arbitrary_type_class = ArbitrarySubType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_validation_fails_for_instance():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    class C:
        pass

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=C)
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'subclass of ArbitraryType expected',
            'type': 'type_error.subclass',
            'ctx': {'expected_class': 'ArbitraryType'},
        }
    ]


def test_type_type_validation_fails_for_basic_type():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=1)
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'subclass of ArbitraryType expected',
            'type': 'type_error.subclass',
            'ctx': {'expected_class': 'ArbitraryType'},
        }
    ]


@pytest.mark.parametrize('bare_type', [type, Type])
def test_bare_type_type_validation_success(bare_type):
    class ArbitraryClassAllowedModel(BaseModel):
        t: bare_type

    arbitrary_type_class = ArbitraryType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


@pytest.mark.parametrize('bare_type', [type, Type])
def test_bare_type_type_validation_fails(bare_type):
    class ArbitraryClassAllowedModel(BaseModel):
        t: bare_type

    arbitrary_type = ArbitraryType()
    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=arbitrary_type)
    assert exc_info.value.errors() == [{'loc': ('t',), 'msg': 'a class is expected', 'type': 'type_error.class'}]


def test_annotation_field_name_shadows_attribute():
    with pytest.raises(NameError):
        # When defining a model that has an attribute with the name of a built-in attribute, an exception is raised
        class BadModel(BaseModel):
            schema: str  # This conflicts with the BaseModel's schema() class method


def test_value_field_name_shadows_attribute():
    # When defining a model that has an attribute with the name of a built-in attribute, an exception is raised
    with pytest.raises(NameError):

        class BadModel(BaseModel):
            schema = 'abc'  # This conflicts with the BaseModel's schema() class method


def test_class_var():
    class MyModel(BaseModel):
        a: ClassVar
        b: ClassVar[int] = 1
        c: int = 2

    assert list(MyModel.__fields__.keys()) == ['c']

    class MyOtherModel(MyModel):
        a = ''
        b = 2

    assert list(MyOtherModel.__fields__.keys()) == ['c']


def test_fields_set():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.__fields_set__ == {'a'}

    m.b = 2
    assert m.__fields_set__ == {'a', 'b'}

    m = MyModel(a=5, b=2)
    assert m.__fields_set__ == {'a', 'b'}


def test_exclude_unset_dict():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.dict(exclude_unset=True) == {'a': 5}

    m = MyModel(a=5, b=3)
    assert m.dict(exclude_unset=True) == {'a': 5, 'b': 3}


def test_exclude_unset_recursive():
    class ModelA(BaseModel):
        a: int
        b: int = 1

    class ModelB(BaseModel):
        c: int
        d: int = 2
        e: ModelA

    m = ModelB(c=5, e={'a': 0})
    assert m.dict() == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert m.dict(exclude_unset=True) == {'c': 5, 'e': {'a': 0}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}


def test_dict_exclude_unset_populated_by_alias():
    class MyModel(BaseModel):
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

        class Config:
            allow_population_by_field_name = True

    m = MyModel(alias_a='a')

    assert m.dict(exclude_unset=True) == {'a': 'a'}
    assert m.dict(exclude_unset=True, by_alias=True) == {'alias_a': 'a'}


def test_dict_exclude_unset_populated_by_alias_with_extra():
    class MyModel(BaseModel):
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

        class Config:
            extra = 'allow'

    m = MyModel(alias_a='a', c='c')

    assert m.dict(exclude_unset=True) == {'a': 'a', 'c': 'c'}
    assert m.dict(exclude_unset=True, by_alias=True) == {'alias_a': 'a', 'c': 'c'}


def test_exclude_defaults():
    class Model(BaseModel):
        mandatory: str
        nullable_mandatory: Optional[str] = ...
        facultative: str = 'x'
        nullable_facultative: Optional[str] = None

    m = Model(mandatory='a', nullable_mandatory=None)
    assert m.dict(exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
    }

    m = Model(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative=None)
    assert m.dict(exclude_defaults=True) == {
        'mandatory': 'a',
        'nullable_mandatory': None,
        'facultative': 'y',
    }

    m = Model(mandatory='a', nullable_mandatory=None, facultative='y', nullable_facultative='z')
    assert m.dict(exclude_defaults=True) == {
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

    assert 'dict' in dir(m)
    assert 'json' in dir(m)
    assert 'attribute_a' in dir(m)
    assert 'attribute_b' in dir(m)


def test_dict_with_extra_keys():
    class MyModel(BaseModel):
        a: str = Field(None, alias='alias_a')

        class Config:
            extra = Extra.allow

    m = MyModel(extra_key='extra')
    assert m.dict() == {'a': None, 'extra_key': 'extra'}
    assert m.dict(by_alias=True) == {'alias_a': None, 'extra_key': 'extra'}


def test_root():
    class MyModel(BaseModel):
        __root__: str

    m = MyModel(__root__='a')
    assert m.dict() == {'__root__': 'a'}
    assert m.__root__ == 'a'


def test_root_list():
    class MyModel(BaseModel):
        __root__: List[str]

    m = MyModel(__root__=['a'])
    assert m.dict() == {'__root__': ['a']}
    assert m.__root__ == ['a']


def test_root_nested():
    class MyList(BaseModel):
        __root__: List[str]

    class MyModel(BaseModel):
        my_list: MyList

    my_list = MyList(__root__=['pika'])
    assert MyModel(my_list=my_list).dict() == {'my_list': ['pika']}


def test_encode_nested_root():
    house_dict = {'pets': ['dog', 'cats']}

    class Pets(BaseModel):
        __root__: List[str]

    class House(BaseModel):
        pets: Pets

    assert House(**house_dict).dict() == house_dict

    class PetsDeep(BaseModel):
        __root__: Pets

    class HouseDeep(BaseModel):
        pets: PetsDeep

    assert HouseDeep(**house_dict).dict() == house_dict


def test_root_failed():
    with pytest.raises(ValueError, match='__root__ cannot be mixed with other fields'):

        class MyModel(BaseModel):
            __root__: str
            a: str


def test_root_undefined_failed():
    class MyModel(BaseModel):
        a: List[str]

    with pytest.raises(ValidationError) as exc_info:
        MyModel(__root__=['a'])
        assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_parse_root_as_mapping():
    class MyModel(BaseModel):
        __root__: Mapping[str, str]

    assert MyModel.parse_obj({1: 2}).__root__ == {'1': '2'}

    with pytest.raises(ValidationError) as exc_info:
        MyModel.parse_obj({'__root__': {'1': '2'}})
    assert exc_info.value.errors() == [
        {'loc': ('__root__', '__root__'), 'msg': 'str type expected', 'type': 'type_error.str'}
    ]


def test_parse_obj_non_mapping_root():
    class MyModel(BaseModel):
        __root__: List[str]

    assert MyModel.parse_obj(['a']).__root__ == ['a']
    assert MyModel.parse_obj({'__root__': ['a']}).__root__ == ['a']
    with pytest.raises(ValidationError) as exc_info:
        MyModel.parse_obj({'__not_root__': ['a']})
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}
    ]
    with pytest.raises(ValidationError):
        MyModel.parse_obj({'__root__': ['a'], 'other': 1})
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}
    ]


def test_parse_obj_nested_root():
    class Pokemon(BaseModel):
        name: str
        level: int

    class Pokemons(BaseModel):
        __root__: List[Pokemon]

    class Player(BaseModel):
        rank: int
        pokemons: Pokemons

    class Players(BaseModel):
        __root__: Dict[str, Player]

    class Tournament(BaseModel):
        players: Players
        city: str

    payload = {
        'players': {
            'Jane': {
                'rank': 1,
                'pokemons': [
                    {
                        'name': 'Pikachu',
                        'level': 100,
                    },
                    {
                        'name': 'Bulbasaur',
                        'level': 13,
                    },
                ],
            },
            'Tarzan': {
                'rank': 2,
                'pokemons': [
                    {
                        'name': 'Jigglypuff',
                        'level': 7,
                    },
                ],
            },
        },
        'city': 'Qwerty',
    }

    tournament = Tournament.parse_obj(payload)
    assert tournament.city == 'Qwerty'
    assert len(tournament.players.__root__) == 2
    assert len(tournament.players.__root__['Jane'].pokemons.__root__) == 2
    assert tournament.players.__root__['Jane'].pokemons.__root__[0].name == 'Pikachu'


def test_untouched_types():
    from pydantic import BaseModel

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    class Model(BaseModel):
        class Config:
            keep_untouched = (classproperty,)

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    assert Model.class_name == 'Model'
    assert Model().class_name == 'Model'


def test_custom_types_fail_without_keep_untouched():
    from pydantic import BaseModel

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    with pytest.raises(RuntimeError) as e:

        class Model(BaseModel):
            @classproperty
            def class_name(cls) -> str:
                return cls.__name__

        Model.class_name

    assert str(e.value) == (
        "no validator found for <class 'tests.test_main.test_custom_types_fail_without_keep_untouched.<locals>."
        "_ClassPropertyDescriptor'>, see `arbitrary_types_allowed` in Config"
    )

    class Model(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    with pytest.raises(AttributeError) as e:
        Model.class_name
    assert str(e.value) == "type object 'Model' has no attribute 'class_name'"


def test_model_iteration():
    class Foo(BaseModel):
        a: int = 1
        b: int = 2

    class Bar(BaseModel):
        c: int
        d: Foo

    m = Bar(c=3, d={})
    assert m.dict() == {'c': 3, 'd': {'a': 1, 'b': 2}}
    assert list(m) == [('c', 3), ('d', Foo())]
    assert dict(m) == {'c': 3, 'd': Foo()}


@pytest.mark.parametrize(
    'exclude,expected,raises_match',
    [
        pytest.param(
            {'foos': {0: {'a'}, 1: {'a'}}},
            {'c': 3, 'foos': [{'b': 2}, {'b': 4}]},
            None,
            id='excluding fields of indexed list items',
        ),
        pytest.param(
            {'foos': {'a'}},
            TypeError,
            'expected integer keys',
            id='should fail trying to exclude string keys on list field (1).',
        ),
        pytest.param(
            {'foos': {0: ..., 'a': ...}},
            TypeError,
            'expected integer keys',
            id='should fail trying to exclude string keys on list field (2).',
        ),
        pytest.param(
            {'foos': {0: 1}},
            TypeError,
            'Unexpected type',
            id='should fail using integer key to specify list item field name (1)',
        ),
        pytest.param(
            {'foos': {'__all__': 1}},
            TypeError,
            'Unexpected type',
            id='should fail using integer key to specify list item field name (2)',
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
            {'foos': {1: {'a'}, -1: {'b'}}},
            {'c': 3, 'foos': [{'a': 1, 'b': 2}, {}]},
            None,
            id='using negative and positive indexes, referencing the same items should merge excludes',
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

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected, match=raises_match):
            m.dict(exclude=exclude)
    else:
        original_exclude = deepcopy(exclude)
        assert m.dict(exclude=exclude) == expected
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
    assert m.dict(exclude=excludes) == expected
    assert excludes == original_excludes


def test_model_exclude_config_field_merging():
    """Test merging field exclude values from config."""

    class Model(BaseModel):
        b: int = Field(2, exclude=...)

        class Config:
            fields = {
                'b': {'exclude': ...},
            }

    assert Model.__fields__['b'].field_info.exclude is ...

    class Model(BaseModel):
        b: int = Field(2, exclude={'a': {'test'}})

        class Config:
            fields = {
                'b': {'exclude': ...},
            }

    assert Model.__fields__['b'].field_info.exclude == {'a': {'test'}}

    class Model(BaseModel):
        b: int = Field(2, exclude={'foo'})

        class Config:
            fields = {
                'b': {'exclude': {'bar'}},
            }

    assert Model.__fields__['b'].field_info.exclude == {'foo': ..., 'bar': ...}


def test_model_exclude_copy_on_model_validation():
    """When `Config.copy_on_model_validation` is set, it should keep private attributes and excluded fields"""

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
    assert my_user.dict() == {'id': 42, 'username': 'JohnDoe', 'hobbies': ['scuba diving']}

    class Transaction(BaseModel):
        id: str
        user: User = Field(..., exclude={'username'})
        value: int

        class Config:
            fields = {'value': {'exclude': True}}

    t = Transaction(
        id='1234567890',
        user=my_user,
        value=9876543210,
    )

    assert t.user is not my_user
    assert t.user.hobbies == ['scuba diving']
    assert t.user.hobbies is my_user.hobbies  # `Config.copy_on_model_validation` does a shallow copy
    assert t.user._priv == 13
    assert t.user.password.get_secret_value() == 'hashedpassword'
    assert t.dict() == {'id': '1234567890', 'user': {'id': 42, 'hobbies': ['scuba diving']}}


def test_model_exclude_copy_on_model_validation_shallow():
    """When `Config.copy_on_model_validation` is set and `Config.copy_on_model_validation_shallow` is set,
    do the same as the previous test but perform a shallow copy"""

    class User(BaseModel):
        class Config:
            copy_on_model_validation = 'shallow'

        hobbies: List[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseModel):
        user: User = Field(...)

    t = Transaction(user=my_user)

    assert t.user is not my_user
    assert t.user.hobbies is my_user.hobbies  # unlike above, this should be a shallow copy


@pytest.mark.parametrize('comv_value', [True, False])
def test_copy_on_model_validation_warning(comv_value):
    class User(BaseModel):
        class Config:
            # True interpreted as 'shallow', False interpreted as 'none'
            copy_on_model_validation = comv_value

        hobbies: List[str]

    my_user = User(hobbies=['scuba diving'])

    class Transaction(BaseModel):
        user: User

    with pytest.warns(DeprecationWarning, match="`copy_on_model_validation` should be a string: 'deep', 'shallow' or"):
        t = Transaction(user=my_user)

    if comv_value:
        assert t.user is not my_user
    else:
        assert t.user is my_user
    assert t.user.hobbies is my_user.hobbies


def test_validation_deep_copy():
    """By default, Config.copy_on_model_validation should do a deep copy"""

    class A(BaseModel):
        name: str

        class Config:
            copy_on_model_validation = 'deep'

    class B(BaseModel):
        list_a: List[A]

    a = A(name='a')
    b = B(list_a=[a])
    assert b.list_a == [A(name='a')]
    a.name = 'b'
    assert b.list_a == [A(name='a')]


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
    assert m.dict(exclude=exclude) == expected, 'Unexpected model export result'


def test_model_export_exclusion_inheritance():
    class Sub(BaseModel):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = Field('v4', exclude=...)

    class Parent(BaseModel):
        a: int
        b: int = Field(..., exclude=...)
        c: int
        d: int
        s: Sub = Sub()

        class Config:
            fields = {'a': {'exclude': ...}, 's': {'exclude': {'s1'}}}

    class Child(Parent):
        class Config:
            fields = {'c': {'exclude': ...}, 's': {'exclude': {'s2'}}}

    actual = Child(a=0, b=1, c=2, d=3).dict()
    expected = {'d': 3, 's': {'s3': 'v3'}}
    assert actual == expected, 'Unexpected model export result'


def test_model_export_with_true_instead_of_ellipsis():
    class Sub(BaseModel):
        s1: int = 1

    class Model(BaseModel):
        a: int = 2
        b: int = Field(3, exclude=True)
        c: int = Field(4)
        s: Sub = Sub()

        class Config:
            fields = {'c': {'exclude': True}}

    m = Model()
    assert m.dict(exclude={'s': True}) == {'a': 2}


def test_model_export_inclusion():
    class Sub(BaseModel):
        s1: str = 'v1'
        s2: str = 'v2'
        s3: str = 'v3'
        s4: str = 'v4'

    class Model(BaseModel):
        a: Sub = Sub()
        b: Sub = Field(Sub(), include={'s1'})
        c: Sub = Field(Sub(), include={'s1', 's2'})

        class Config:
            fields = {'a': {'include': {'s2', 's1', 's3'}}, 'b': {'include': {'s1', 's2', 's3', 's4'}}}

    Model.__fields__['a'].field_info.include == {'s1': ..., 's2': ..., 's3': ...}
    Model.__fields__['b'].field_info.include == {'s1': ...}
    Model.__fields__['c'].field_info.include == {'s1': ..., 's2': ...}

    actual = Model().dict(include={'a': {'s3', 's4'}, 'b': ..., 'c': ...})
    # s1 included via field, s2 via config and s3 via .dict call:
    expected = {'a': {'s3': 'v3'}, 'b': {'s1': 'v1'}, 'c': {'s1': 'v1', 's2': 'v2'}}

    assert actual == expected, 'Unexpected model export result'


def test_model_export_inclusion_inheritance():
    class Sub(BaseModel):
        s1: str = Field('v1', include=...)
        s2: str = Field('v2', include=...)
        s3: str = Field('v3', include=...)
        s4: str = 'v4'

    class Parent(BaseModel):
        a: int
        b: int
        c: int
        s: Sub = Field(Sub(), include={'s1', 's2'})  # overrides includes set in Sub model

        class Config:
            # b will be included since fields are set idependently
            fields = {'b': {'include': ...}}

    class Child(Parent):
        class Config:
            # b is still included even if it doesn't occur here since fields
            # are still considered separately.
            # s however, is merged, resulting in only s1 being included.
            fields = {'a': {'include': ...}, 's': {'include': {'s1'}}}

    actual = Child(a=0, b=1, c=2).dict()
    expected = {'a': 0, 'b': 1, 's': {'s1': 'v1'}}
    assert actual == expected, 'Unexpected model export result'


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
        something = 1

    assert NewModel.something == 2


def test_update_forward_refs_does_not_modify_module_dict():
    class MyModel(BaseModel):
        field: Optional['MyModel']  # noqa: F821

    MyModel.update_forward_refs()

    assert 'MyModel' not in sys.modules[MyModel.__module__].__dict__


def test_two_defaults():
    with pytest.raises(ValueError, match='^cannot specify both default and default_factory$'):

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
        singleton: MySingleton = Field(default_factory=lambda: MY_SINGLETON)

        class Config:
            arbitrary_types_allowed = True

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

    assert exc_info.value.errors() == [
        {'loc': ('children', 1, 'x'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_default_factory_parse():
    class Inner(BaseModel):
        val: int = Field(0)

    class Outer(BaseModel):
        inner_1: Inner = Field(default_factory=Inner)
        inner_2: Inner = Field(Inner())

    default = Outer().dict()
    parsed = Outer.parse_obj(default)
    assert parsed.dict() == {'inner_1': {'val': 0}, 'inner_2': {'val': 0}}
    assert repr(parsed) == 'Outer(inner_1=Inner(val=0), inner_2=Inner(val=0))'


def test_none_min_max_items():
    # None default
    class Foo(BaseModel):
        foo: List = Field(None)
        bar: List = Field(None, min_items=0)
        baz: List = Field(None, max_items=10)

    f1 = Foo()
    f2 = Foo(bar=None)
    f3 = Foo(baz=None)
    f4 = Foo(bar=None, baz=None)
    for f in (f1, f2, f3, f4):
        assert f.foo is None
        assert f.bar is None
        assert f.baz is None


def test_reuse_same_field():
    required_field = Field(...)

    class Model1(BaseModel):
        required: str = required_field

    class Model2(BaseModel):
        required: str = required_field

    with pytest.raises(ValidationError):
        Model1.parse_obj({})
    with pytest.raises(ValidationError):
        Model2.parse_obj({})


def test_base_config_type_hinting():
    class M(BaseModel):
        a: int

    get_type_hints(M.__config__)


def test_allow_mutation_field():
    """assigning a allow_mutation=False field should raise a TypeError"""

    class Entry(BaseModel):
        id: float = Field(allow_mutation=False)
        val: float

        class Config:
            validate_assignment = True

    r = Entry(id=1, val=100)
    assert r.val == 100
    r.val = 101
    assert r.val == 101
    assert r.id == 1
    with pytest.raises(TypeError, match='"id" has allow_mutation set to False and cannot be assigned'):
        r.id = 2


def test_repr_field():
    class Model(BaseModel):
        a: int = Field()
        b: int = Field(repr=True)
        c: int = Field(repr=False)

    m = Model(a=1, b=2, c=3)
    assert repr(m) == 'Model(a=1, b=2)'
    assert repr(m.__fields__['a'].field_info) == 'FieldInfo(default=PydanticUndefined, extra={})'
    assert repr(m.__fields__['b'].field_info) == 'FieldInfo(default=PydanticUndefined, extra={})'
    assert repr(m.__fields__['c'].field_info) == 'FieldInfo(default=PydanticUndefined, repr=False, extra={})'


def test_inherited_model_field_copy():
    """It should copy models used as fields by default"""

    class Image(BaseModel):
        path: str

        def __hash__(self):
            return id(self)

    class Item(BaseModel):
        images: List[Image]

    image_1 = Image(path='my_image1.png')
    image_2 = Image(path='my_image2.png')

    item = Item(images={image_1, image_2})
    assert image_1 in item.images

    assert id(image_1) != id(item.images[0])
    assert id(image_2) != id(item.images[1])


def test_inherited_model_field_untouched():
    """It should not copy models used as fields if explicitly asked"""

    class Image(BaseModel):
        path: str

        def __hash__(self):
            return id(self)

        class Config:
            copy_on_model_validation = 'none'

    class Item(BaseModel):
        images: List[Image]

    image_1 = Image(path='my_image1.png')
    image_2 = Image(path='my_image2.png')

    item = Item(images=(image_1, image_2))
    assert image_1 in item.images

    assert id(image_1) == id(item.images[0])
    assert id(image_2) == id(item.images[1])


def test_mapping_retains_type_subclass():
    class CustomMap(dict):
        pass

    class Model(BaseModel):
        x: Mapping[str, Mapping[str, int]]

    m = Model(x=CustomMap(outer=CustomMap(inner=42)))
    assert isinstance(m.x, CustomMap)
    assert isinstance(m.x['outer'], CustomMap)
    assert m.x['outer']['inner'] == 42


def test_mapping_retains_type_defaultdict():
    class Model(BaseModel):
        x: Mapping[str, int]

    d = defaultdict(int)
    d[1] = '2'
    d['3']

    m = Model(x=d)
    assert isinstance(m.x, defaultdict)
    assert m.x['1'] == 2
    assert m.x['3'] == 0


def test_mapping_retains_type_fallback_error():
    class CustomMap(dict):
        def __init__(self, *args, **kwargs):
            if args or kwargs:
                raise TypeError('test')
            super().__init__(*args, **kwargs)

    class Model(BaseModel):
        x: Mapping[str, int]

    d = CustomMap()
    d['one'] = 1
    d['two'] = 2

    with pytest.raises(RuntimeError, match="Could not convert dictionary to 'CustomMap'"):
        Model(x=d)


def test_typing_coercion_dict():
    class Model(BaseModel):
        x: Dict[str, int]

    m = Model(x={'one': 1, 'two': 2})
    assert repr(m) == "Model(x={'one': 1, 'two': 2})"


def test_typing_non_coercion_of_dict_subclasses():
    KT = TypeVar('KT')
    VT = TypeVar('VT')

    class MyDict(Dict[KT, VT]):
        def __repr__(self):
            return f'MyDict({super().__repr__()})'

    class Model(BaseModel):
        a: MyDict
        b: MyDict[str, int]
        c: Dict[str, int]
        d: Mapping[str, int]

    assert (
        repr(Model(a=MyDict({'a': 1}), b=MyDict({'a': '1'}), c=MyDict({'a': '1'}), d=MyDict({'a': '1'})))
        == "Model(a=MyDict({'a': 1}), b=MyDict({'a': 1}), c={'a': 1}, d=MyDict({'a': 1}))"
    )


def test_typing_coercion_defaultdict():
    class Model(BaseModel):
        x: DefaultDict[int, str]

    d = defaultdict(str)
    d['1']
    m = Model(x=d)
    m.x['a']
    assert repr(m) == "Model(x=defaultdict(<class 'str'>, {1: '', 'a': ''}))"


def test_typing_coercion_counter():
    class Model(BaseModel):
        x: Counter[str]

    assert Model.__fields__['x'].type_ is int
    assert repr(Model(x={'a': 10})) == "Model(x=Counter({'a': 10}))"


def test_typing_counter_value_validation():
    class Model(BaseModel):
        x: Counter[str]

    with pytest.raises(ValidationError) as exc_info:
        Model(x={'a': 'a'})

    assert exc_info.value.errors() == [
        {
            'loc': ('x', 'a'),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        }
    ]


def test_class_kwargs_config():
    class Base(BaseModel, extra='forbid', alias_generator=str.upper):
        a: int

    assert Base.__config__.extra is Extra.forbid
    assert Base.__config__.alias_generator is str.upper
    assert Base.__fields__['a'].alias == 'A'

    class Model(Base, extra='allow'):
        b: int

    assert Model.__config__.extra is Extra.allow  # overwritten as intended
    assert Model.__config__.alias_generator is str.upper  # inherited as intended
    assert Model.__fields__['b'].alias == 'B'  # alias_generator still works


def test_class_kwargs_config_json_encoders():
    class Model(BaseModel, json_encoders={int: str}):
        pass

    assert Model.__config__.json_encoders == {int: str}


def test_class_kwargs_config_and_attr_conflict():
    with pytest.raises(
        TypeError, match='Specifying config in two places is ambiguous, use either Config attribute or class kwargs'
    ):

        class Model(BaseModel, extra='allow'):
            b: int

            class Config:
                extra = 'forbid'


def test_class_kwargs_custom_config():
    class Base(BaseModel):
        class Config(BaseConfig):
            some_config = 'value'

    class Model(Base, some_config='new_value'):
        a: int

    assert Model.__config__.some_config == 'new_value'


@pytest.mark.skipif(sys.version_info < (3, 10), reason='need 3.10 version')
def test_new_union_origin():
    """On 3.10+, origin of `int | str` is `types.UnionType`, not `typing.Union`"""

    class Model(BaseModel):
        x: int | str

    assert Model(x=3).x == 3
    assert Model(x='3').x == 3
    assert Model(x='pika').x == 'pika'
    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'x': {'title': 'X', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
        'required': ['x'],
    }


def test_annotated_class():
    class PydanticModel(BaseModel):
        foo: str = '123'

    PydanticAlias = Annotated[PydanticModel, 'bar baz']

    pa = PydanticAlias()
    assert isinstance(pa, PydanticModel)
    pa.__doc__ = 'qwe'
    assert repr(pa) == "PydanticModel(foo='123')"
    assert pa.__doc__ == 'qwe'


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
def test_final_field_decl_withou_default_val(ann, value):
    class Model(BaseModel):
        a: ann

        if value is not None:
            a = value

    Model.update_forward_refs(ann=ann)

    assert 'a' not in Model.__class_vars__
    assert 'a' in Model.__fields__

    assert Model.__fields__['a'].final


@pytest.mark.parametrize(
    'ann',
    [Final, Final[int]],
    ids=['no-arg', 'with-arg'],
)
def test_final_field_decl_with_default_val(ann):
    class Model(BaseModel):
        a: ann = 10

    Model.update_forward_refs(ann=ann)

    assert 'a' in Model.__class_vars__
    assert 'a' not in Model.__fields__


def test_final_field_reassignment():
    class Model(BaseModel):
        a: Final[int]

    obj = Model(a=10)

    with pytest.raises(
        TypeError,
        match=r'^"Model" object "a" field is final and does not support reassignment$',
    ):
        obj.a = 20


def test_field_by_default_is_not_final():
    class Model(BaseModel):
        a: int

    assert not Model.__fields__['a'].final
