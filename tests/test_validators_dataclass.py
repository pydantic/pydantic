from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytest

from pydantic import ValidationError, errors, validator
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


def test_int_validation():
    @dataclass
    class MyDataclass:
        a: int

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a='snap')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert MyDataclass(a=3).a == 3
    assert MyDataclass(a=True).a == 1
    assert MyDataclass(a=False).a == 0
    assert MyDataclass(a=4.5).a == 4


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


def test_validate_kwargs():
    @dataclass
    class MyDataclass:
        b: int
        a: List[int]

        @validator('a')
        def check_a1(cls, v, values, **kwargs):
            return v + values['b']

    assert MyDataclass(a=[1, 2], b=6).a == [7, 8]


def test_validate_whole_error():
    calls = []

    @dataclass
    class MyDataclass:
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

    assert MyDataclass(a=[3, 8]).a == [4, 8]
    assert calls == ['check_a1 [3, 8]', 'check_a2 [4, 8]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a=[1, 3])
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'a1 broken', 'type': 'value_error'}]
    assert calls == ['check_a1 [1, 3]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a=[5, 10])
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'a2 broken', 'type': 'value_error'}]
    assert calls == ['check_a1 [5, 10]', 'check_a2 [6, 10]']


class Config:
    validate_assignment = True


@dataclass(config=Config)
class ValidateAssignmentDataclass:
    a: int = 4
    b: str = ...

    @validator('b')
    def b_length(cls, v, values, **kwargs):
        if 'a' in values and len(v) < values['a']:
            raise ValueError('b too short')
        return v


def test_validating_assignment_ok():
    p = ValidateAssignmentDataclass(b='hello')
    assert p.b == 'hello'


def test_validating_assignment_fail():
    with pytest.raises(ValidationError):
        ValidateAssignmentDataclass(a=10, b='hello')

    p = ValidateAssignmentDataclass(b='hello')
    with pytest.raises(ValidationError):
        p.b = 'x'


def test_validating_assignment_dict():
    with pytest.raises(ValidationError) as exc_info:
        ValidateAssignmentDataclass(a='x', b='xx')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


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


def test_duplicates():
    with pytest.raises(errors.ConfigError) as exc_info:

        @dataclass
        class MyDataclass:
            a: str
            b: str

            @validator('a')
            def duplicate_name(cls, v):
                return v

            @validator('b')  # noqa
            def duplicate_name(cls, v):  # noqa
                return v

    assert str(exc_info.value) == (
        'duplicate validator function '
        '"tests.test_validators_dataclass.test_duplicates.<locals>.MyDataclass.duplicate_name"'
    )


def test_use_bare():
    with pytest.raises(errors.ConfigError) as exc_info:

        @dataclass
        class MyDataclass:
            a: str

            @validator
            def checker(cls, v):
                return v

    assert 'validators should be used with fields' in str(exc_info.value)


def test_use_no_fields():
    with pytest.raises(errors.ConfigError) as exc_info:

        @dataclass
        class MyDataclass:
            a: str

            @validator()
            def checker(cls, v):
                return v

    assert 'validator with no fields specified' in str(exc_info.value)


def test_validate_always():
    check_calls = 0

    @dataclass
    class MyDataclass:
        a: str = None

        @validator('a', pre=True, always=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert MyDataclass().a == 'xxx'
    assert check_calls == 1
    assert MyDataclass(a='y').a == 'y'
    assert check_calls == 2


def test_validate_not_always():
    check_calls = 0

    @dataclass
    class MyDataclass:
        a: str = None

        @validator('a', pre=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert MyDataclass().a is None
    assert check_calls == 0
    assert MyDataclass(a='y').a == 'y'
    assert check_calls == 1


def test_wildcard_validators():
    calls = []

    @dataclass
    class MyDataclass:
        a: str
        b: int

        @validator('a')
        def check_a(cls, v, field, **kwargs):
            calls.append(('check_a', v, field.name))
            return v

        @validator('*')
        def check_all(cls, v, field, **kwargs):
            calls.append(('check_all', v, field.name))
            return v

    assert asdict(MyDataclass(a='abc', b='123')) == dict(a='abc', b=123)
    assert calls == [('check_a', 'abc', 'a'), ('check_all', 'abc', 'a'), ('check_all', 123, 'b')]


def test_wildcard_validator_error():
    @dataclass
    class MyDataclass:
        a: str
        b: str

        @validator('*')
        def check_all(cls, v, field, **kwargs):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert MyDataclass(a='foobar a', b='foobar b').b == 'foobar b'

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass(a='snap', b="foobar b")
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': '"foobar" not found in a', 'type': 'value_error'}]


def test_invalid_field():
    with pytest.raises(errors.ConfigError) as exc_info:

        @dataclass
        class MyDataclass:
            a: str

            @validator('b')
            def check_b(cls, v):
                return v

    assert str(exc_info.value) == (
        "Validators defined with incorrect fields: check_b "
        "(use check_fields=False if you're inheriting from the model and intended this)"
    )


def test_validate_child():
    @dataclass
    class Parent:
        a: str

    @dataclass
    class Child(Parent):
        @validator('a')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Parent(a='this is not a child').a == 'this is not a child'
    assert Child(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_child_extra():
    @dataclass
    class Parent:
        a: str

        @validator('a')
        def check_a_one(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    @dataclass
    class Child(Parent):
        @validator('a')
        def check_a_two(cls, v):
            return v.upper()

    assert Parent(a='this is foobar good').a == 'this is foobar good'
    assert Child(a='this is foobar good').a == 'THIS IS FOOBAR GOOD'
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_child_all():
    @dataclass
    class Parent:
        a: str

    @dataclass
    class Child(Parent):
        @validator('*')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Parent(a='this is not a child').a == 'this is not a child'
    assert Child(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        Child(a='snap')


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


def test_validate_parent_all():
    @dataclass
    class Parent:
        a: str

        @validator('*')
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


def test_inheritance_keep():
    @dataclass
    class Parent:
        a: int

        @validator('a')
        def add_to_a(cls, v):
            return v + 1

    @dataclass
    class Child(Parent):
        pass

    assert Child(a=0).a == 1


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


def test_inheritance_new():
    @dataclass
    class Parent:
        a: int

        @validator('a')
        def add_one_to_a(cls, v):
            return v + 1

    @dataclass
    class Child(Parent):
        @validator('a')
        def add_five_to_a(cls, v):
            return v + 5

    assert Child(a=0).a == 6


def test_no_key_validation():
    @dataclass
    class MyDataclass:
        foobar: Dict[int, int]

        @validator('foobar')
        def check_foobar(cls, v):
            return v + 1

    assert MyDataclass(foobar={1: 1}).foobar == {1: 2}


def test_key_validation_whole():
    @dataclass
    class MyDataclass:
        foobar: Dict[int, int]

        @validator('foobar', whole=True)
        def check_foobar(cls, value):
            return {k + 1: v + 1 for k, v in value.items()}

    assert MyDataclass(foobar={1: 1}).foobar == {2: 2}


def test_validator_always_optional():
    check_calls = 0

    @dataclass
    class MyDataclass:
        a: Optional[str] = None

        @validator('a', pre=True, always=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or 'default value'

    assert MyDataclass(a='y').a == 'y'
    assert check_calls == 1
    assert MyDataclass().a == 'default value'
    assert check_calls == 2


def test_validator_always_post():
    @dataclass
    class MyDataclass:
        a: str = None

        @validator('a', always=True)
        def check_a(cls, v):
            return v or 'default value'

    assert MyDataclass(a='y').a == 'y'
    with pytest.raises(ValidationError):
        MyDataclass()


def test_validator_always_post_optional():
    @dataclass
    class MyDataclass:
        a: Optional[str] = None

        @validator('a', always=True)
        def check_a(cls, v):
            return v or 'default value'

    assert MyDataclass(a='y').a == 'y'
    assert MyDataclass().a == 'default value'


def test_datetime_validator():
    check_calls = 0

    @dataclass
    class MyDataclass:
        d: datetime = None

        @validator('d', pre=True, always=True)
        def check_d(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or datetime(2032, 1, 1)

    assert MyDataclass(d='2023-01-01T00:00:00').d == datetime(2023, 1, 1)
    assert check_calls == 1
    assert MyDataclass().d == datetime(2032, 1, 1)
    assert check_calls == 2
    assert MyDataclass(d=datetime(2023, 1, 1)).d == datetime(2023, 1, 1)
    assert check_calls == 3


def test_whole_called_once():
    check_calls = 0

    @dataclass
    class MyDataclass:
        a: Tuple[int, int, int]

        @validator('a', pre=True, whole=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v

    assert MyDataclass(a=['1', '2', '3']).a == (1, 2, 3)
    assert check_calls == 1
