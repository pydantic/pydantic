import re
from collections import deque
from datetime import datetime
from enum import Enum
from itertools import product
from typing import Any, Deque, Dict, FrozenSet, List, Optional, Tuple, Type, Union
from unittest.mock import MagicMock

import pytest
from typing_extensions import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Extra,
    Field,
    FieldValidationInfo,
    ValidationError,
    errors,
    validator,
)
from pydantic.decorators import field_validator, root_validator


def test_simple():
    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Model(a='this is foobar good').a == 'this is foobar good'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': ('a',),
            'msg': 'Value error, "foobar" not found in a',
            'input': 'snap',
            'ctx': {'error': '"foobar" not found in a'},
        }
    ]


def test_int_validation():
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'snap',
        }
    ]
    assert Model(a=3).a == 3
    assert Model(a=True).a == 1
    assert Model(a=False).a == 0
    with pytest.raises(ValidationError) as exc_info:
        Model(a=4.5)
    assert exc_info.value.errors() == [
        {
            'type': 'int_from_float',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, got a number with a fractional part',
            'input': 4.5,
        }
    ]


@pytest.mark.parametrize('value', [2.2250738585072011e308, float('nan'), float('inf')])
def test_int_overflow_validation(value):
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    assert exc_info.value.errors() == [
        {'type': 'finite_number', 'loc': ('a',), 'msg': 'Input should be a finite number', 'input': value}
    ]


def test_frozenset_validation():
    class Model(BaseModel):
        a: FrozenSet[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {'type': 'frozen_set_type', 'loc': ('a',), 'msg': 'Input should be a valid frozenset', 'input': 'snap'}
    ]
    assert Model(a={1, 2, 3}).a == frozenset({1, 2, 3})
    assert Model(a=frozenset({1, 2, 3})).a == frozenset({1, 2, 3})
    assert Model(a=[4, 5]).a == frozenset({4, 5})
    assert Model(a=(6,)).a == frozenset({6})
    assert Model(a={'1', '2', '3'}).a == frozenset({1, 2, 3})


def test_deque_validation():
    class Model(BaseModel):
        a: Deque[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': ('a',), 'msg': 'Input should be a valid list', 'input': 'snap'}
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(a=['a'])
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(a=('a',))
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(a={'1'})
    assert exc_info.value.errors() == [
        {'type': 'list_type', 'loc': ('a',), 'msg': 'Input should be a valid list', 'input': {'1'}}
    ]
    assert Model(a=[4, 5]).a == deque([4, 5])
    assert Model(a=(6,)).a == deque([6])


def test_validate_whole():
    class Model(BaseModel):
        a: List[int]

        @field_validator('a', mode='before')
        @classmethod
        def check_a1(cls, v: List[Any]) -> List[Any]:
            v.append('123')
            return v

        @field_validator('a')
        @classmethod
        def check_a2(cls, v: List[int]) -> List[Any]:
            v.append(456)
            return v

    assert Model(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_pre_error():
    calls = []

    class Model(BaseModel):
        a: List[int]

        @field_validator('a', mode='before')
        @classmethod
        def check_a1(cls, v: Any):
            calls.append(f'check_a1 {v}')
            if 1 in v:
                raise ValueError('a1 broken')
            v[0] += 1
            return v

        @field_validator('a')
        @classmethod
        def check_a2(cls, v: Any):
            calls.append(f'check_a2 {v}')
            if 10 in v:
                raise ValueError('a2 broken')
            return v

    assert Model(a=[3, 8]).a == [4, 8]
    assert calls == ['check_a1 [3, 8]', 'check_a2 [4, 8]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[1, 3])
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': ('a',),
            'msg': 'Value error, a1 broken',
            'input': [1, 3],
            'ctx': {'error': 'a1 broken'},
        }
    ]
    assert calls == ['check_a1 [1, 3]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[5, 10])
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': ('a',),
            'msg': 'Value error, a2 broken',
            'input': [6, 10],
            'ctx': {'error': 'a2 broken'},
        }
    ]
    assert calls == ['check_a1 [5, 10]', 'check_a2 [6, 10]']


@pytest.fixture(scope='session', name='ValidateAssignmentModel')
def validate_assignment_model_fixture():
    class ValidateAssignmentModel(BaseModel):
        a: int = 4
        b: str = ...
        c: int = 0

        @field_validator('b')
        @classmethod
        def b_length(cls, v, info):
            values = info.data
            if 'a' in values and len(v) < values['a']:
                raise ValueError('b too short')
            return v

        @field_validator('c')
        @classmethod
        def double_c(cls, v: Any):
            return v * 2

        model_config = ConfigDict(validate_assignment=True, extra=Extra.allow)

    return ValidateAssignmentModel


def test_validating_assignment_ok(ValidateAssignmentModel):
    p = ValidateAssignmentModel(b='hello')
    assert p.b == 'hello'


def test_validating_assignment_fail(ValidateAssignmentModel):
    with pytest.raises(ValidationError):
        ValidateAssignmentModel(a=10, b='hello')

    p = ValidateAssignmentModel(b='hello')
    with pytest.raises(ValidationError):
        p.b = 'x'


def test_validating_assignment_value_change(ValidateAssignmentModel):
    p = ValidateAssignmentModel(b='hello', c=2)
    assert p.c == 4

    p = ValidateAssignmentModel(b='hello')
    assert p.c == 0
    p.c = 3
    assert p.c == 6


def test_validating_assignment_extra(ValidateAssignmentModel):
    p = ValidateAssignmentModel(b='hello', extra_field=1.23)
    assert p.extra_field == 1.23

    p = ValidateAssignmentModel(b='hello')
    p.extra_field = 1.23
    assert p.extra_field == 1.23
    p.extra_field = 'bye'
    assert p.extra_field == 'bye'


def test_validating_assignment_dict(ValidateAssignmentModel):
    with pytest.raises(ValidationError) as exc_info:
        ValidateAssignmentModel(a='x', b='xx')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        }
    ]


def test_validating_assignment_values_dict():
    class ModelOne(BaseModel):
        a: int

    class ModelTwo(BaseModel):
        m: ModelOne
        b: int

        @field_validator('b')
        @classmethod
        def validate_b(cls, b, info: FieldValidationInfo):
            if 'm' in info.data:
                return b + info.data['m'].a  # this fails if info.data['m'] is a dict
            else:
                return b

        model_config = ConfigDict(validate_assignment=True)

    model = ModelTwo(m=ModelOne(a=1), b=2)
    assert model.b == 3
    model.b = 3
    assert model.b == 4


def test_validate_multiple():
    class Model(BaseModel):
        a: str
        b: str

        @field_validator('a', 'b')
        @classmethod
        def check_a_and_b(cls, v: Any, info: FieldValidationInfo) -> Any:
            if len(v) < 4:
                field = cls.model_fields[info.field_name]
                raise AssertionError(f'{field.alias or info.field_name} is too short')
            return v + 'x'

    assert Model(a='1234', b='5678').model_dump() == {'a': '1234x', 'b': '5678x'}

    with pytest.raises(ValidationError) as exc_info:
        Model(a='x', b='x')
    assert exc_info.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': ('a',),
            'msg': 'Assertion failed, a is too short',
            'input': 'x',
            'ctx': {'error': 'a is too short'},
        },
        {
            'type': 'assertion_error',
            'loc': ('b',),
            'msg': 'Assertion failed, b is too short',
            'input': 'x',
            'ctx': {'error': 'b is too short'},
        },
    ]


def test_classmethod():
    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            assert cls is Model
            return v

    m = Model(a='this is foobar good')
    assert m.a == 'this is foobar good'
    m.check_a('x')


def test_duplicates():
    msg = r'duplicate validator function \"tests.test_validators::test_duplicates.<locals>.Model.duplicate_name\";'
    with pytest.warns(UserWarning, match=msg):

        class Model(BaseModel):
            a: str
            b: str

            @field_validator('a')
            def duplicate_name(cls, v: Any):
                return v

            @field_validator('b')
            def duplicate_name(cls, v: Any):  # noqa
                return v


def test_use_bare():
    with pytest.raises(TypeError, match='validators should be used with fields'):

        class Model(BaseModel):
            a: str

            with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

                @validator
                def checker(cls, v):
                    return v


def test_use_bare_field_validator():
    with pytest.raises(TypeError, match='field_validators should be used with fields'):

        class Model(BaseModel):
            a: str

            @field_validator
            def checker(cls, v):
                return v


def test_use_no_fields():
    with pytest.raises(TypeError, match=re.escape("validator() missing 1 required positional argument: '__field'")):

        class Model(BaseModel):
            a: str

            with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

                @validator()
                def checker(cls, v):
                    return v


def test_use_no_fields_field_validator():
    with pytest.raises(
        TypeError, match=re.escape("field_validator() missing 1 required positional argument: '__field'")
    ):

        class Model(BaseModel):
            a: str

            @field_validator()
            def checker(cls, v):
                return v


def test_validator_bad_fields_throws_configerror():
    """
    Attempts to create a validator with fields set as a list of strings,
    rather than just multiple string args. Expects ConfigError to be raised.
    """
    with pytest.raises(TypeError, match='validator fields should be passed as separate string args.'):

        class Model(BaseModel):
            a: str
            b: str

            with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

                @validator(['a', 'b'])
                def check_fields(cls, v):
                    return v


def test_field_validator_bad_fields_throws_configerror():
    """
    Attempts to create a validator with fields set as a list of strings,
    rather than just multiple string args. Expects ConfigError to be raised.
    """
    with pytest.raises(TypeError, match='field_validator fields should be passed as separate string args.'):

        class Model(BaseModel):
            a: str
            b: str

            @field_validator(['a', 'b'])
            def check_fields(cls, v):
                return v


def test_validate_always():
    check_calls = 0

    class Model(BaseModel):
        a: str = None

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', pre=True, always=True)
            @classmethod
            def check_a(cls, v: Any):
                nonlocal check_calls
                check_calls += 1
                return v or 'xxx'

    assert Model().a == 'xxx'
    assert check_calls == 1
    assert Model(a='y').a == 'y'
    assert check_calls == 2


def test_field_validator_validate_default():
    check_calls = 0

    class Model(BaseModel):
        a: str = Field(None, validate_default=True)

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert Model().a == 'xxx'
    assert check_calls == 1
    assert Model(a='y').a == 'y'
    assert check_calls == 2


def test_validate_always_on_inheritance():
    check_calls = 0

    class ParentModel(BaseModel):
        a: str = None

    class Model(ParentModel):
        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', pre=True, always=True)
            @classmethod
            def check_a(cls, v: Any):
                nonlocal check_calls
                check_calls += 1
                return v or 'xxx'

    assert Model().a == 'xxx'
    assert check_calls == 1
    assert Model(a='y').a == 'y'
    assert check_calls == 2


def test_field_validator_validate_default_on_inheritance():
    check_calls = 0

    class ParentModel(BaseModel):
        a: str = Field(None, validate_default=True)

    class Model(ParentModel):
        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert Model().a == 'xxx'
    assert check_calls == 1
    assert Model(a='y').a == 'y'
    assert check_calls == 2


def test_validate_not_always():
    check_calls = 0

    class Model(BaseModel):
        a: Optional[str] = None

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert Model().a is None
    assert check_calls == 0
    assert Model(a='y').a == 'y'
    assert check_calls == 1


def test_wildcard_validators():
    calls: list[tuple[str, Any]] = []

    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: str
            b: int

            @validator('a')
            def check_a(cls, v: Any) -> Any:
                calls.append(('check_a', v))
                return v

            @validator('*')
            def check_all(cls, v: Any) -> Any:
                calls.append(('check_all', v))
                return v

    assert Model(a='abc', b='123').model_dump() == dict(a='abc', b=123)
    assert calls == [('check_a', 'abc'), ('check_all', 'abc'), ('check_all', 123)]


def test_wildcard_validator_error():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: str
            b: str

            @validator('*')
            def check_all(cls, v: Any) -> Any:
                if 'foobar' not in v:
                    raise ValueError('"foobar" not found in a')
                return v

    assert Model(a='foobar a', b='foobar b').b == 'foobar b'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')

    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': ('a',),
            'msg': 'Value error, "foobar" not found in a',
            'input': 'snap',
            'ctx': {'error': '"foobar" not found in a'},
        },
        {'type': 'missing', 'loc': ('b',), 'msg': 'Field required', 'input': {'a': 'snap'}},
    ]


def test_invalid_field():
    with pytest.raises(errors.PydanticUserError) as exc_info:

        class Model(BaseModel):
            a: str

            @field_validator('b')
            def check_b(cls, v: Any):
                return v

    assert str(exc_info.value) == (
        "Validators defined with incorrect fields: check_b "
        "(use check_fields=False if you're inheriting from the model and intended this)"
    )


def test_validate_child():
    class Parent(BaseModel):
        a: str

    class Child(Parent):
        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Parent(a='this is not a child').a == 'this is not a child'
    assert Child(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_child_extra():
    class Parent(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a_one(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    class Child(Parent):
        @field_validator('a')
        @classmethod
        def check_a_two(cls, v: Any):
            return v.upper()

    assert Parent(a='this is foobar good').a == 'this is foobar good'
    assert Child(a='this is foobar good').a == 'THIS IS FOOBAR GOOD'
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_child_all():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Parent(BaseModel):
            a: str

        class Child(Parent):
            @validator('*')
            @classmethod
            def check_a(cls, v: Any):
                if 'foobar' not in v:
                    raise ValueError('"foobar" not found in a')
                return v

        assert Parent(a='this is not a child').a == 'this is not a child'
        assert Child(a='this is foobar good').a == 'this is foobar good'
        with pytest.raises(ValidationError):
            Child(a='snap')


def test_validate_parent():
    class Parent(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    class Child(Parent):
        pass

    assert Parent(a='this is foobar good').a == 'this is foobar good'
    assert Child(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        Parent(a='snap')
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_parent_all():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Parent(BaseModel):
            a: str

            @validator('*')
            @classmethod
            def check_a(cls, v: Any):
                if 'foobar' not in v:
                    raise ValueError('"foobar" not found in a')
                return v

        class Child(Parent):
            pass

        assert Parent(a='this is foobar good').a == 'this is foobar good'
        assert Child(a='this is foobar good').a == 'this is foobar good'
        with pytest.raises(ValidationError):
            Parent(a='snap')
        with pytest.raises(ValidationError):
            Child(a='snap')


def test_inheritance_keep():
    class Parent(BaseModel):
        a: int

        @field_validator('a')
        @classmethod
        def add_to_a(cls, v: Any):
            return v + 1

    class Child(Parent):
        pass

    assert Child(a=0).a == 1


def test_inheritance_replace():
    """We promise that if you add a validator
    with the same _function_ name as an existing validator
    it replaces the existing validator and is run instead of it.
    """

    class Parent(BaseModel):
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

    assert Parent(a=[]).a == ['parent before', 'parent', 'parent after']
    assert Child(a=[]).a == ['parent before', 'child', 'parent after', 'child before', 'child after']


def test_inheritance_replace_root_validator():
    """
    We promise that if you add a validator
    with the same _function_ name as an existing validator
    it replaces the existing validator and is run instead of it.
    """

    class Parent(BaseModel):
        a: List[str]

        @root_validator(skip_on_failure=True)
        def parent_val_before(cls, values: Dict[str, Any]):
            values['a'].append('parent before')
            return values

        @root_validator(skip_on_failure=True)
        def val(cls, values: Dict[str, Any]):
            values['a'].append('parent')
            return values

        @root_validator(skip_on_failure=True)
        def parent_val_after(cls, values: Dict[str, Any]):
            values['a'].append('parent after')
            return values

    class Child(Parent):
        @root_validator(skip_on_failure=True)
        def child_val_before(cls, values: Dict[str, Any]):
            values['a'].append('child before')
            return values

        @root_validator(skip_on_failure=True)
        def val(cls, values: Dict[str, Any]):
            values['a'].append('child')
            return values

        @root_validator(skip_on_failure=True)
        def child_val_after(cls, values: Dict[str, Any]):
            values['a'].append('child after')
            return values

    assert Parent(a=[]).a == ['parent before', 'parent', 'parent after']
    assert Child(a=[]).a == ['parent before', 'child', 'parent after', 'child before', 'child after']


def test_validation_each_item():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            foobar: Dict[int, int]

            @validator('foobar', each_item=True)
            @classmethod
            def check_foobar(cls, v: Any):
                return v + 1

    assert Model(foobar={1: 1}).foobar == {1: 2}


def test_validation_each_item_nullable():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            foobar: Optional[List[int]]

            @validator('foobar', each_item=True)
            @classmethod
            def check_foobar(cls, v: Any):
                return v + 1

    assert Model(foobar=[1]).foobar == [2]


def test_validation_each_item_one_sublevel():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            foobar: List[Tuple[int, int]]

            @validator('foobar', each_item=True)
            @classmethod
            def check_foobar(cls, v: Tuple[int, int]) -> Tuple[int, int]:
                v1, v2 = v
                assert v1 == v2
                return v

    assert Model(foobar=[(1, 1), (2, 2)]).foobar == [(1, 1), (2, 2)]


def test_key_validation():
    class Model(BaseModel):
        foobar: Dict[int, int]

        @field_validator('foobar')
        @classmethod
        def check_foobar(cls, value):
            return {k + 1: v + 1 for k, v in value.items()}

    assert Model(foobar={1: 1}).foobar == {2: 2}


def test_validator_always_optional():
    check_calls = 0

    class Model(BaseModel):
        a: Optional[str] = None

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', pre=True, always=True)
            @classmethod
            def check_a(cls, v: Any):
                nonlocal check_calls
                check_calls += 1
                return v or 'default value'

    assert Model(a='y').a == 'y'
    assert check_calls == 1
    assert Model().a == 'default value'
    assert check_calls == 2


def test_field_validator_validate_default_optional():
    check_calls = 0

    class Model(BaseModel):
        a: Optional[str] = Field(None, validate_default=True)

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert check_calls == 1
    assert Model().a == 'default value'
    assert check_calls == 2


def test_validator_always_pre():
    check_calls = 0

    class Model(BaseModel):
        a: str = None

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', pre=True, always=True)
            @classmethod
            def check_a(cls, v: Any):
                nonlocal check_calls
                check_calls += 1
                return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'
    assert check_calls == 2


def test_field_validator_validate_default_pre():
    check_calls = 0

    class Model(BaseModel):
        a: str = Field(None, validate_default=True)

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'
    assert check_calls == 2


def test_validator_always_post():
    class Model(BaseModel):
        # NOTE: Unlike in v1, you can't replicate the behavior of only applying defined validators and not standard
        # field validation. This is why I've set the default to '' instead of None.
        # But, I think this is a good thing, and I don't think we should try to support this.
        a: str = ''

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', always=True)
            @classmethod
            def check_a(cls, v: Any):
                return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_field_validator_validate_default_post():
    class Model(BaseModel):
        a: str = Field('', validate_default=True)

        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_validator_always_post_optional():
    class Model(BaseModel):
        a: Optional[str] = None

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('a', pre=True, always=True)
            @classmethod
            def check_a(cls, v: Any):
                return 'default value' if v is None else v

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_field_validator_validate_default_post_optional():
    class Model(BaseModel):
        a: Optional[str] = Field(None, validate_default=True)

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_datetime_validator():
    check_calls = 0

    class Model(BaseModel):
        d: datetime = None

        with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

            @validator('d', pre=True, always=True)
            @classmethod
            def check_d(cls, v: Any):
                nonlocal check_calls
                check_calls += 1
                return v or datetime(2032, 1, 1)

    assert Model(d='2023-01-01T00:00:00').d == datetime(2023, 1, 1)
    assert check_calls == 1
    assert Model().d == datetime(2032, 1, 1)
    assert check_calls == 2
    assert Model(d=datetime(2023, 1, 1)).d == datetime(2023, 1, 1)
    assert check_calls == 3


def test_datetime_field_validator():
    check_calls = 0

    class Model(BaseModel):
        d: datetime = Field(None, validate_default=True)

        @field_validator('d', mode='before')
        @classmethod
        def check_d(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v or datetime(2032, 1, 1)

    assert Model(d='2023-01-01T00:00:00').d == datetime(2023, 1, 1)
    assert check_calls == 1
    assert Model().d == datetime(2032, 1, 1)
    assert check_calls == 2
    assert Model(d=datetime(2023, 1, 1)).d == datetime(2023, 1, 1)
    assert check_calls == 3


def test_pre_called_once():
    check_calls = 0

    class Model(BaseModel):
        a: Tuple[int, int, int]

        @field_validator('a', mode='before')
        @classmethod
        def check_a(cls, v: Any):
            nonlocal check_calls
            check_calls += 1
            return v

    assert Model(a=['1', '2', '3']).a == (1, 2, 3)
    assert check_calls == 1


def test_assert_raises_validation_error():
    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls, v: Any):
            assert v == 'a', 'invalid a'
            return v

    Model(a='a')

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    injected_by_pytest = "assert 'snap' == 'a'\n  - a\n  + snap"
    assert exc_info.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': ('a',),
            'msg': f'Assertion failed, invalid a\n{injected_by_pytest}',
            'input': 'snap',
            'ctx': {'error': "invalid a\nassert 'snap' == 'a'\n  - a\n  + snap"},
        }
    ]


def test_root_validator():
    root_val_values: List[Dict[str, Any]] = []

    class Model(BaseModel):
        a: int = 1
        b: str
        c: str

        @field_validator('b')
        @classmethod
        def repeat_b(cls, v: Any):
            return v * 2

        @root_validator(skip_on_failure=True)
        def example_root_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

        @root_validator(skip_on_failure=True)
        def example_root_validator2(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            root_val_values.append(values)
            if 'snap' in values.get('c', ''):
                raise ValueError('foobar2')
            return dict(values, c='changed')

    assert Model(a='123', b='bar', c='baz').model_dump() == {'a': 123, 'b': 'changed', 'c': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon', c='snap dragon2')
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': {'b': 'snap dragon', 'c': 'snap dragon2'},
            'ctx': {'error': 'foobar'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='broken', b='bar', c='baz')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'broken',
        }
    ]

    assert root_val_values == [
        {'a': 123, 'b': 'barbar', 'c': 'baz'},
        {'a': 123, 'b': 'changed', 'c': 'baz'},
        {'a': 1, 'b': 'snap dragonsnap dragon', 'c': 'snap dragon2'},
    ]


def test_root_validator_pre():
    root_val_values: List[Dict[str, Any]] = []

    class Model(BaseModel):
        a: int = 1
        b: str

        @field_validator('b')
        @classmethod
        def repeat_b(cls, v: Any):
            return v * 2

        @root_validator(pre=True)
        def root_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return {'a': 42, 'b': 'changed'}

    assert Model(a='123', b='bar').model_dump() == {'a': 42, 'b': 'changedchanged'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon')

    assert root_val_values == [{'a': '123', 'b': 'bar'}, {'b': 'snap dragon'}]
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': {'b': 'snap dragon'},
            'ctx': {'error': 'foobar'},
        }
    ]


def test_root_validator_repeat():
    with pytest.warns(UserWarning, match='duplicate validator function'):

        class Model(BaseModel):
            a: int = 1

            @root_validator(skip_on_failure=True)
            def root_validator_repeated(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore
                return values

            @root_validator(skip_on_failure=True)
            def root_validator_repeated(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # noqa: F811
                return values


def test_root_validator_repeat2():
    with pytest.warns(UserWarning, match='duplicate validator function'):

        class Model(BaseModel):
            a: int = 1

            @field_validator('a')
            def repeat_validator(cls, v: Any) -> Any:  # type: ignore
                return v

            @root_validator(skip_on_failure=True)
            def repeat_validator(cls, values: Any) -> Any:  # noqa: F811
                return values


def test_root_validator_types():
    root_val_values: Optional[Tuple[Type[BaseModel], Dict[str, Any]]] = None

    class Model(BaseModel):
        a: int = 1
        b: str

        @root_validator(skip_on_failure=True)
        def root_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal root_val_values
            root_val_values = cls, values
            return values

        model_config = ConfigDict(extra=Extra.allow)

    assert Model(b='bar', c='wobble').model_dump() == {'a': 1, 'b': 'bar', 'c': 'wobble'}

    assert root_val_values == (Model, {'a': 1, 'b': 'bar', 'c': 'wobble'})


def test_root_validator_returns_none_exception():
    class Model(BaseModel):
        a: int = 1

        @root_validator(skip_on_failure=True)
        def root_validator_repeated(cls, values):
            return None

    with pytest.raises(
        TypeError,
        match=r"(:?__dict__ must be set to a dictionary, not a 'NoneType')|(:?setting dictionary to a non-dict)",
    ):
        Model()


def reusable_validator(num: int) -> int:
    return num * 2


def test_reuse_global_validators():
    class Model(BaseModel):
        x: int
        y: int

        double_x = field_validator('x', allow_reuse=True)(reusable_validator)
        double_y = field_validator('y', allow_reuse=True)(reusable_validator)

    assert dict(Model(x=1, y=1)) == {'x': 2, 'y': 2}


def declare_with_reused_validators(include_root, allow_1, allow_2, allow_3):
    class Model(BaseModel):
        a: str
        b: str

        @field_validator('a', allow_reuse=allow_1)
        @classmethod
        def duplicate_name(cls, v: Any):
            return v

        @field_validator('b', allow_reuse=allow_2)
        @classmethod
        def duplicate_name(cls, v: Any):  # noqa F811
            return v

        if include_root:

            @root_validator(allow_reuse=allow_3, skip_on_failure=True)
            def duplicate_name(cls, values):  # noqa F811
                return values


@pytest.fixture
def reset_tracked_validators():
    from pydantic._internal._decorators import _FUNCS

    original_tracked_validators = set(_FUNCS)
    yield
    _FUNCS.clear()
    _FUNCS.update(original_tracked_validators)


@pytest.mark.parametrize('include_root,allow_1,allow_2,allow_3', product(*[[True, False]] * 4))
def test_allow_reuse(include_root, allow_1, allow_2, allow_3, reset_tracked_validators):
    duplication_count = int(not allow_1) + int(not allow_2) + int(include_root and not allow_3)
    if duplication_count > 1:
        with pytest.warns(UserWarning, match='duplicate validator function'):
            declare_with_reused_validators(include_root, allow_1, allow_2, allow_3)
    else:
        declare_with_reused_validators(include_root, allow_1, allow_2, allow_3)


@pytest.mark.parametrize('validator_classmethod,root_validator_classmethod', product(*[[True, False]] * 2))
def test_root_validator_classmethod(validator_classmethod, root_validator_classmethod, reset_tracked_validators):
    root_val_values = []

    class Model(BaseModel):
        a: int = 1
        b: str

        def repeat_b(cls, v: Any):
            return v * 2

        if validator_classmethod:
            repeat_b = classmethod(repeat_b)
        repeat_b = field_validator('b')(repeat_b)

        def example_root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

        if root_validator_classmethod:
            example_root_validator = classmethod(example_root_validator)
        example_root_validator = root_validator(skip_on_failure=True)(example_root_validator)

    assert Model(a='123', b='bar').model_dump() == {'a': 123, 'b': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon')
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': {'b': 'snap dragon'},
            'ctx': {'error': 'foobar'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='broken', b='bar')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'broken',
        }
    ]

    assert root_val_values == [{'a': 123, 'b': 'barbar'}, {'a': 1, 'b': 'snap dragonsnap dragon'}]


def test_assignment_validator_cls():
    validator_calls = 0

    class Model(BaseModel):
        name: str

        model_config = ConfigDict(validate_assignment=True)

        @field_validator('name')
        @classmethod
        def check_foo(cls, value):
            nonlocal validator_calls
            validator_calls += 1
            assert cls == Model
            return value

    m = Model(name='hello')
    m.name = 'goodbye'
    assert validator_calls == 2


def test_literal_validator():
    class Model(BaseModel):
        a: Literal['foo']

    Model(a='foo')

    with pytest.raises(ValidationError) as exc_info:
        Model(a='nope')
    assert exc_info.value.errors() == [
        {
            'type': 'literal_error',
            'loc': ('a',),
            'msg': "Input should be 'foo'",
            'input': 'nope',
            'ctx': {'expected': "'foo'"},
        }
    ]


@pytest.mark.xfail(reason='working on V2 - enum validator bug https://github.com/pydantic/pydantic/issues/5242')
def test_literal_validator_str_enum():
    class Bar(str, Enum):
        FIZ = 'fiz'
        FUZ = 'fuz'

    class Foo(BaseModel):
        bar: Bar
        barfiz: Literal[Bar.FIZ]
        fizfuz: Literal[Bar.FIZ, Bar.FUZ]

    my_foo = Foo.model_validate({'bar': 'fiz', 'barfiz': 'fiz', 'fizfuz': 'fiz'})
    assert my_foo.bar is Bar.FIZ
    # TODO: this doesn't pass, `my_foo.barfiz == 'fiz'`
    # Is this an intentional behavior change?
    assert my_foo.barfiz is Bar.FIZ
    assert my_foo.fizfuz is Bar.FIZ

    my_foo = Foo.model_validate({'bar': 'fiz', 'barfiz': 'fiz', 'fizfuz': 'fuz'})
    assert my_foo.bar is Bar.FIZ
    assert my_foo.barfiz is Bar.FIZ
    assert my_foo.fizfuz is Bar.FUZ


def test_nested_literal_validator():
    L1 = Literal['foo']
    L2 = Literal['bar']

    class Model(BaseModel):
        a: Literal[L1, L2]

    Model(a='foo')

    with pytest.raises(ValidationError) as exc_info:
        Model(a='nope')
    assert exc_info.value.errors() == [
        {
            'type': 'literal_error',
            'loc': ('a',),
            'msg': "Input should be 'foo' or 'bar'",
            'input': 'nope',
            'ctx': {'expected': "'foo' or 'bar'"},
        }
    ]


# TODO: this test fails because our union schema
# doesn't accept `frozen` as an argument
# Do we need to add `frozen` to every schema?
@pytest.mark.xfail(reason='frozen field')
def test_union_literal_with_constraints():
    class Model(BaseModel, validate_assignment=True):
        x: Union[Literal[42], Literal['pika']] = Field(frozen=True)

    m = Model(x=42)
    with pytest.raises(TypeError):
        m.x += 1


def test_field_that_is_being_validated_is_excluded_from_validator_values():
    check_values = MagicMock()

    class Model(BaseModel):
        foo: str
        bar: str = Field(alias='pika')
        baz: str

        model_config = ConfigDict(validate_assignment=True)

        @field_validator('foo')
        @classmethod
        def validate_foo(cls, v: Any, info: FieldValidationInfo) -> Any:
            check_values({**info.data})
            return v

        @field_validator('bar')
        @classmethod
        def validate_bar(cls, v: Any, info: FieldValidationInfo) -> Any:
            check_values({**info.data})
            return v

    model = Model(foo='foo_value', pika='bar_value', baz='baz_value')
    check_values.reset_mock()

    assert list(dict(model).items()) == [('foo', 'foo_value'), ('bar', 'bar_value'), ('baz', 'baz_value')]

    model.foo = 'new_foo_value'
    check_values.assert_called_once_with({'bar': 'bar_value', 'baz': 'baz_value'})
    check_values.reset_mock()

    model.bar = 'new_bar_value'
    check_values.assert_called_once_with({'foo': 'new_foo_value', 'baz': 'baz_value'})

    # ensure field order is the same
    assert list(dict(model).items()) == [('foo', 'new_foo_value'), ('bar', 'new_bar_value'), ('baz', 'baz_value')]


def test_exceptions_in_field_validators_restore_original_field_value():
    class Model(BaseModel):
        foo: str

        model_config = ConfigDict(validate_assignment=True)

        @field_validator('foo')
        @classmethod
        def validate_foo(cls, v: Any):
            if v == 'raise_exception':
                raise RuntimeError('test error')
            return v

    model = Model(foo='foo')
    with pytest.raises(RuntimeError, match='test error'):
        model.foo = 'raise_exception'
    assert model.foo == 'foo'


def test_overridden_root_validators():
    validate_stub = MagicMock()

    class A(BaseModel):
        x: str

        @root_validator(pre=True)
        def pre_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            validate_stub('A', 'pre')
            return values

        @root_validator(pre=False, skip_on_failure=True)
        def post_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            validate_stub('A', 'post')
            return values

    class B(A):
        @root_validator(pre=True)
        def pre_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            validate_stub('B', 'pre')
            return values

        @root_validator(pre=False, skip_on_failure=True)
        def post_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            validate_stub('B', 'post')
            return values

    A(x='pika')
    assert validate_stub.call_args_list == [[('A', 'pre'), {}], [('A', 'post'), {}]]

    validate_stub.reset_mock()

    B(x='pika')
    assert validate_stub.call_args_list == [[('B', 'pre'), {}], [('B', 'post'), {}]]


def test_validating_assignment_pre_root_validator_fail():
    class Model(BaseModel):
        current_value: float = Field(..., alias='current')
        max_value: float

        model_config = ConfigDict(validate_assignment=True)

        @root_validator(pre=True)
        def values_are_not_string(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            if any(isinstance(x, str) for x in values.values()):
                raise ValueError('values cannot be a string')
            return values

    m = Model(current=100, max_value=200)
    with pytest.raises(ValidationError) as exc_info:
        m.current_value = '100'
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, values cannot be a string',
            'input': {'current_value': '100', 'max_value': 200.0},
            'ctx': {'error': 'values cannot be a string'},
        }
    ]


@pytest.mark.parametrize(
    'kwargs',
    [
        {'skip_on_failure': False},
        {'skip_on_failure': False, 'pre': False},
        {'pre': False},
    ],
)
def test_root_validator_skip_on_failure_invalid(kwargs: Dict[str, Any]):
    with pytest.raises(TypeError, match='MUST specify `skip_on_failure=True`'):

        class Model(BaseModel):
            @root_validator(**kwargs)
            def root_val(cls, values: Dict[str, Any]) -> Dict[str, Any]:
                return values


@pytest.mark.parametrize(
    'kwargs',
    [
        {'skip_on_failure': True},
        {'skip_on_failure': True, 'pre': False},
        {'skip_on_failure': False, 'pre': True},
        {'pre': True},
    ],
)
def test_root_validator_skip_on_failure_valid(kwargs: Dict[str, Any]):
    class Model(BaseModel):
        @root_validator(**kwargs, allow_reuse=True)
        def root_val(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            return values


def test_root_validator_many_values_change():
    """It should run root_validator on assignment and update ALL concerned fields"""

    class Rectangle(BaseModel):
        width: float
        height: float
        area: Optional[float] = None

        model_config = ConfigDict(validate_assignment=True)

        @root_validator(skip_on_failure=True, allow_reuse=True)
        def set_area(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            values['area'] = values['width'] * values['height']
            return values

    r = Rectangle(width=1, height=1)
    assert r.area == 1
    r.height = 5
    assert r.area == 5


V1_VALIDATOR_DEPRECATION_MATCH = r'Pydantic V1 style `@validator` validators are deprecated'


def _get_source_line(filename: str, lineno: int) -> str:
    with open(filename) as f:
        for _ in range(lineno - 1):
            f.readline()
        return f.readline()


def test_v1_validator_deprecated():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH) as w:

        class Point(BaseModel):
            y: int
            x: int

            @validator('x')
            @classmethod
            def check_x(cls, x: int, values: Dict[str, Any]) -> int:
                assert x * 2 == values['y']
                return x

    assert Point(x=1, y=2).model_dump() == {'x': 1, 'y': 2}

    warnings = w.list
    assert len(warnings) == 1
    w = warnings[0]
    # check that we got stacklevel correct
    # if this fails you need to edit the stacklevel
    # parameter to warnings.warn in _decorators.py
    assert w.filename == __file__
    source = _get_source_line(w.filename, w.lineno)
    # the reported location varies slightly from 3.7 to 3.11
    assert 'check_x' in source or "@validator('x')" in source


def test_info_field_name_data_before():
    """
    Test accessing info.field_name and info.data
    We only test the `before` validator because they
    all share the same implementation.
    """

    class Model(BaseModel):
        a: str
        b: str

        @field_validator('b', mode='before')
        @classmethod
        def check_a(cls, v: Any, info: FieldValidationInfo) -> Any:
            assert v == b'but my barbaz is better'
            assert info.field_name == 'b'
            assert info.data == {'a': 'your foobar is good'}
            return 'just kidding!'

    assert Model(a=b'your foobar is good', b=b'but my barbaz is better').b == 'just kidding!'


def test_decorator_proxy():
    """
    Test that our validator decorator allows
    calling the wrapped methods/functions.
    """

    def val(v: int) -> int:
        return v + 1

    class Model(BaseModel):
        x: int

        @field_validator('x')
        @staticmethod
        def val1(v: int) -> int:
            return v + 1

        @field_validator('x')
        @classmethod
        def val2(cls, v: int) -> int:
            return v + 1

        val3 = field_validator('x')(val)

    assert Model.val1(1) == 2
    assert Model.val2(1) == 2
    assert Model.val3(1) == 2


def test_root_validator_self():
    with pytest.raises(TypeError, match=r'`@root_validator` cannot be applied to instance methods'):

        class Model(BaseModel):
            a: int = 1

            @root_validator(skip_on_failure=True)
            def root_validator(self, values: Any) -> Any:
                return values


def test_validator_self():
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):
        with pytest.raises(TypeError, match=r'`@validator` cannot be applied to instance methods'):

            class Model(BaseModel):
                a: int = 1

                @validator('a')
                def check_a(self, values: Any) -> Any:
                    return values


def test_field_validator_self():
    with pytest.raises(TypeError, match=r'`@field_validator` cannot be applied to instance methods'):

        class Model(BaseModel):
            a: int = 1

            @field_validator('a')
            def check_a(self, values: Any) -> Any:
                return values


def test_v1_validator_signature_kwargs_not_allowed() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):
        with pytest.raises(TypeError, match=r'Unsupported signature for V1 style validator'):

            class Model(BaseModel):
                a: int

                @validator('a')
                def check_a(cls, value: Any, foo: Any) -> Any:
                    ...


def test_v1_validator_signature_kwargs1() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: int
            b: int

            @validator('b')
            def check_b(cls, value: Any, **kwargs: Any) -> Any:
                assert kwargs == {'values': {'a': 1}}
                assert value == 2
                return value + 1

    assert Model(a=1, b=2).model_dump() == {'a': 1, 'b': 3}


def test_v1_validator_signature_kwargs2() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: int
            b: int

            @validator('b')
            def check_b(cls, value: Any, values: Dict[str, Any], **kwargs: Any) -> Any:
                assert kwargs == {}
                assert values == {'a': 1}
                assert value == 2
                return value + 1

    assert Model(a=1, b=2).model_dump() == {'a': 1, 'b': 3}


def test_v1_validator_signature_with_values() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: int
            b: int

            @validator('b')
            def check_b(cls, value: Any, values: Dict[str, Any]) -> Any:
                assert values == {'a': 1}
                assert value == 2
                return value + 1

    assert Model(a=1, b=2).model_dump() == {'a': 1, 'b': 3}


def test_v1_validator_signature_with_values_kw_only() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):

        class Model(BaseModel):
            a: int
            b: int

            @validator('b')
            def check_b(cls, value: Any, *, values: Dict[str, Any]) -> Any:
                assert values == {'a': 1}
                assert value == 2
                return value + 1

    assert Model(a=1, b=2).model_dump() == {'a': 1, 'b': 3}


def test_v1_validator_signature_with_field() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):
        with pytest.raises(TypeError, match=r'The `field` and `config` parameters are not available in Pydantic V2'):

            class Model(BaseModel):
                a: int
                b: int

                @validator('b')
                def check_b(cls, value: Any, field: Any) -> Any:
                    ...


def test_v1_validator_signature_with_config() -> None:
    with pytest.warns(DeprecationWarning, match=V1_VALIDATOR_DEPRECATION_MATCH):
        with pytest.raises(TypeError, match=r'The `field` and `config` parameters are not available in Pydantic V2'):

            class Model(BaseModel):
                a: int
                b: int

                @validator('b')
                def check_b(cls, value: Any, config: Any) -> Any:
                    ...


def test_model_config_validate_default():
    class Model(BaseModel):
        x: int = -1

        @field_validator('x')
        @classmethod
        def force_x_positive(cls, v):
            assert v > 0
            return v

    assert Model().x == -1

    class ValidatingModel(Model):
        model_config = ConfigDict(validate_default=True)

    with pytest.raises(ValidationError) as exc_info:
        ValidatingModel()
    assert exc_info.value.errors() == [
        {
            'ctx': {'error': 'assert -1 > 0'},
            'input': -1,
            'loc': ('x',),
            'msg': 'Assertion failed, assert -1 > 0',
            'type': 'assertion_error',
        }
    ]
