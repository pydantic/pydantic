from typing import List

import pytest

from pydantic import BaseModel, ConfigError, ValidationError, validator


def test_simple():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert '"foobar" not found in a' in str(exc_info.value)


def test_validate_whole():
    class Model(BaseModel):
        a: List[int]

        @validator('a', whole=True, pre=True)
        def check_a1(cls, v):
            v.append('123')
            return v

        @validator('a', whole=True)
        def check_a2(cls, v):
            v.append(456)
            return v

    assert Model(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_kwargs():
    class Model(BaseModel):
        b: int
        a: List[int]

        @validator('a')
        def check_a1(cls, v, values, **kwargs):
            return v + values['b']

    assert Model(a=[1, 2], b=6).a == [7, 8]


def test_validate_whole_error():
    calls = []

    class Model(BaseModel):
        a: List[int]

        @validator('a', whole=True, pre=True)
        def check_a1(cls, v):
            calls.append(f'check_a1 {v}')
            if 1 in v:
                raise ValueError('a1 broken')
            v[0] += 1
            return v

        @validator('a', whole=True)
        def check_a2(cls, v):
            calls.append(f'check_a2 {v}')
            if 10 in v:
                raise ValueError('a2 broken')
            return v

    assert Model(a=[3, 8]).a == [4, 8]
    assert calls == ['check_a1 [3, 8]', 'check_a2 [4, 8]']
    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[1, 3])
    assert 'a1 broken' in str(exc_info.value)
    assert calls == ['check_a1 [1, 3]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[5, 10])
    assert 'a2 broken' in str(exc_info.value)
    assert calls == ['check_a1 [5, 10]', 'check_a2 [6, 10]']


class ValidateAssignmentModel(BaseModel):
    a: int = 4
    b: str = ...

    @validator('b')
    def b_length(cls, v, values, **kwargs):
        if 'a' in values and len(v) < values['a']:
            raise ValueError('b too short')
        return v

    class Config:
        validate_assignment = True


def test_validating_assignment_ok():
    p = ValidateAssignmentModel(b='hello')
    assert p.b == 'hello'


def test_validating_assignment_fail():
    with pytest.raises(ValidationError):
        ValidateAssignmentModel(a=10, b='hello')

    p = ValidateAssignmentModel(b='hello')
    with pytest.raises(ValidationError):
        p.b = 'x'


def test_validating_assignment_dict():
    with pytest.raises(ValidationError) as exc_info:
        ValidateAssignmentModel(a='x', b='xx')
    assert """\
error validating input
a:
  invalid literal for int() with base 10: 'x' (error_type=ValueError track=int)""" == str(exc_info.value)


def test_validate_multiple():
    # also test TypeError
    class Model(BaseModel):
        a: str
        b: str

        @validator('a', 'b')
        def check_a_and_b(cls, v, field, **kwargs):
            if len(v) < 4:
                raise TypeError(f'{field.alias} is too short')
            return v + 'x'

    assert Model(a='1234', b='5678').dict() == {'a': '1234x', 'b': '5678x'}
    with pytest.raises(ValidationError) as exc_info:
        Model(a='x', b='x')
    assert """\
2 errors validating input
a:
  a is too short (error_type=TypeError track=str)
b:
  b is too short (error_type=TypeError track=str)""" == str(exc_info.value)


def test_classmethod():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            assert cls is Model
            return v

    m = Model(a='this is foobar good')
    assert m.a == 'this is foobar good'
    m.check_a('x')


def test_duplicates():
    with pytest.raises(ConfigError) as exc_info:
        class Model(BaseModel):
            a: str
            b: str

            @validator('a')
            def duplicate_name(cls, v):
                return v

            @validator('b')  # noqa
            def duplicate_name(cls, v):
                return v
    assert str(exc_info.value) == ('duplicate validator function '
                                   '"tests.test_validators.test_duplicates.<locals>.Model.duplicate_name"')
