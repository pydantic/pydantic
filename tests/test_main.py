from enum import Enum
from typing import Any, List

import pytest

from pydantic import BaseModel, NoneBytes, NoneStr, Required, ValidationError, constr, errors


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


class UltraSimpleModel(BaseModel):
    a: float = ...
    b: int = 10


def test_ultra_simple_missing():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'field required',
            'type': 'value_error.missing',
        },
    ]


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'value is not a valid float',
            'type': 'type_error.float',
        },
        {
            'loc': ('b',),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert repr(m) == '<UltraSimpleModel a=10.2 b=10>'
    assert repr(m.fields['a']) == "<Field(a type=float required)>"
    assert dict(m) == {'a': 10.2, 'b': 10}


def test_str_truncate():
    class Model(BaseModel):
        s1: str
        s2: str
        b1: bytes
        b2: bytes

    m = Model(s1='132', s2='x' * 100, b1='123', b2='x' * 100)
    print(repr(m.to_string()))
    assert m.to_string() == ("Model s1='132' "
                             "s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…' "
                             "b1=b'123' "
                             "b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…")
    assert """\
Model
  s1='132'
  s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…'
  b1=b'123'
  b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…""" == m.to_string(pretty=True)


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
        required_str_value='v1',
        required_str_none_value=None,
        required_bytes_value='v2',
        required_bytes_none_value=None,
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
        {
            'loc': ('required_str_value',),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
        {
            'loc': ('required_bytes_value',),
            'msg': 'none is not an allow value',
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
    assert repr(m) == '<RecursiveModel grape=True banana=<UltraSimpleModel a=1.0 b=10>>'


def test_recursion_fails():
    with pytest.raises(ValidationError):
        RecursiveModel(grape=1, banana=123)


class PreventExtraModel(BaseModel):
    foo = 'whatever'

    class Config:
        ignore_extra = False


def test_prevent_extra_success():
    m = PreventExtraModel()
    assert m.foo == 'whatever'

    m = PreventExtraModel(foo=1)
    assert m.foo == '1'


def test_prevent_extra_fails():
    with pytest.raises(ValidationError) as exc_info:
        PreventExtraModel(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.errors() == [
        {
            'loc': ('bar',),
            'msg': 'extra fields not permitted',
            'type': 'value_error.extra',
        },
        {
            'loc': ('spam',),
            'msg': 'extra fields not permitted',
            'type': 'value_error.extra',
        },
    ]


class InvalidValidator:
    @classmethod
    def get_validators(cls):
        yield cls.has_wrong_arguments

    @classmethod
    def has_wrong_arguments(cls, value, bar):
        pass


def test_invalid_validator():
    with pytest.raises(errors.ConfigError) as exc_info:
        class InvalidValidatorModel(BaseModel):
            x: InvalidValidator = ...
    assert exc_info.value.args[0].startswith('Invalid signature for validator')


def test_no_validator():
    with pytest.raises(errors.ConfigError) as exc_info:
        class NoValidatorModel(BaseModel):
            x: object = ...
    assert exc_info.value.args[0] == "no validator found for <class 'object'>"


def test_unable_to_infer():
    with pytest.raises(errors.ConfigError) as exc_info:
        class InvalidDefinitionModel(BaseModel):
            x = None
    assert exc_info.value.args[0] == 'unable to infer type for attribute "x"'


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
            allow_extra = True

    assert Model(a='10.2', b=12).dict() == {'a': 10.2, 'b': 12}


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
    assert '"UltraSimpleModel" object has no field "c"' in str(exc_info)


def test_any():
    class AnyModel(BaseModel):
        a: Any = 10

    assert AnyModel().a == 10
    assert AnyModel(a='foobar').a == 'foobar'


def test_alias():
    class Model(BaseModel):
        a = 'foobar'

        class Config:
            fields = {
                'a': {'alias': '_a'}
            }

    assert Model().a == 'foobar'
    assert Model().dict() == {'a': 'foobar'}
    assert Model(_a='different').a == 'different'
    assert Model(_a='different').dict() == {'a': 'different'}


def test_population_by_alias():
    class Model(BaseModel):
        a: str

        class Config:
            allow_population_by_alias = True
            fields = {
                'a': {'alias': '_a'}
            }

    assert Model(a='different').a == 'different'
    assert Model(a='different').dict() == {'a': 'different'}


def test_field_order():
    class Model(BaseModel):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    # fields are ordered as defined except annotation-only fields come last
    assert list(Model.__fields__.keys()) == ['c', 'a', 'b', 'd']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float = Required
        b: int = 10

    m = Model(a=10.2)
    assert m.dict() == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'field required',
            'type': 'value_error.missing',
        },
    ]


def test_not_immutability():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = True
            allow_extra = False

    m = TestModel()
    assert m.a == 10
    m.a = 11
    assert m.a == 11
    with pytest.raises(ValueError) as exc_info:
        m.b = 11
    assert '"TestModel" object has no field "b"' in str(exc_info)


def test_immutability():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = False
            allow_extra = False

    m = TestModel()
    assert m.a == 10
    with pytest.raises(TypeError) as exc_info:
        m.a = 11
    assert '"TestModel" is immutable and does not support item assignment' in str(exc_info)
    with pytest.raises(ValueError) as exc_info:
        m.b = 11
    assert '"TestModel" object has no field "b"' in str(exc_info)


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
        {
            'loc': ('a',),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        p.b = ''
    assert exc_info.value.errors() == [
        {
            'loc': ('b',),
            'msg': 'ensure this value has at least 1 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {
                'limit_value': 1,
            },
        },
    ]


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
