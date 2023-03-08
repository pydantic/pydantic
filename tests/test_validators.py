from collections import deque
from datetime import datetime
from enum import Enum
from functools import partial, partialmethod
from itertools import product
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pytest
from typing_extensions import Literal

from pydantic import BaseModel, ConfigError, Extra, Field, ValidationError, conlist, errors, validator
from pydantic.class_validators import make_generic_validator, root_validator


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
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': '"foobar" not found in a', 'type': 'value_error'}]


def test_int_validation():
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert Model(a=3).a == 3
    assert Model(a=True).a == 1
    assert Model(a=False).a == 0
    assert Model(a=4.5).a == 4


@pytest.mark.parametrize('value', [2.2250738585072011e308, float('nan'), float('inf')])
def test_int_overflow_validation(value):
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_frozenset_validation():
    class Model(BaseModel):
        a: frozenset

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid frozenset', 'type': 'type_error.frozenset'}
    ]
    assert Model(a={1, 2, 3}).a == frozenset({1, 2, 3})
    assert Model(a=frozenset({1, 2, 3})).a == frozenset({1, 2, 3})
    assert Model(a=[4, 5]).a == frozenset({4, 5})
    assert Model(a=(6,)).a == frozenset({6})


def test_deque_validation():
    class Model(BaseModel):
        a: deque

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'value is not a valid deque', 'type': 'type_error.deque'}]
    assert Model(a={1, 2, 3}).a == deque([1, 2, 3])
    assert Model(a=deque({1, 2, 3})).a == deque([1, 2, 3])
    assert Model(a=[4, 5]).a == deque([4, 5])
    assert Model(a=(6,)).a == deque([6])


def test_validate_whole():
    class Model(BaseModel):
        a: List[int]

        @validator('a', pre=True)
        def check_a1(cls, v):
            v.append('123')
            return v

        @validator('a')
        def check_a2(cls, v):
            v.append(456)
            return v

    assert Model(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_kwargs():
    class Model(BaseModel):
        b: int
        a: List[int]

        @validator('a', each_item=True)
        def check_a1(cls, v, values, **kwargs):
            return v + values['b']

    assert Model(a=[1, 2], b=6).a == [7, 8]


def test_validate_pre_error():
    calls = []

    class Model(BaseModel):
        a: List[int]

        @validator('a', pre=True)
        def check_a1(cls, v):
            calls.append(f'check_a1 {v}')
            if 1 in v:
                raise ValueError('a1 broken')
            v[0] += 1
            return v

        @validator('a')
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
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'a1 broken', 'type': 'value_error'}]
    assert calls == ['check_a1 [1, 3]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[5, 10])
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'a2 broken', 'type': 'value_error'}]
    assert calls == ['check_a1 [5, 10]', 'check_a2 [6, 10]']


class ValidateAssignmentModel(BaseModel):
    a: int = 4
    b: str = ...
    c: int = 0

    @validator('b')
    def b_length(cls, v, values, **kwargs):
        if 'a' in values and len(v) < values['a']:
            raise ValueError('b too short')
        return v

    @validator('c')
    def double_c(cls, v):
        return v * 2

    class Config:
        validate_assignment = True
        extra = Extra.allow


def test_validating_assignment_ok():
    p = ValidateAssignmentModel(b='hello')
    assert p.b == 'hello'


def test_validating_assignment_fail():
    with pytest.raises(ValidationError):
        ValidateAssignmentModel(a=10, b='hello')

    p = ValidateAssignmentModel(b='hello')
    with pytest.raises(ValidationError):
        p.b = 'x'


def test_validating_assignment_value_change():
    p = ValidateAssignmentModel(b='hello', c=2)
    assert p.c == 4

    p = ValidateAssignmentModel(b='hello')
    assert p.c == 0
    p.c = 3
    assert p.c == 6


def test_validating_assignment_extra():
    p = ValidateAssignmentModel(b='hello', extra_field=1.23)
    assert p.extra_field == 1.23

    p = ValidateAssignmentModel(b='hello')
    p.extra_field = 1.23
    assert p.extra_field == 1.23
    p.extra_field = 'bye'
    assert p.extra_field == 'bye'


def test_validating_assignment_dict():
    with pytest.raises(ValidationError) as exc_info:
        ValidateAssignmentModel(a='x', b='xx')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_validating_assignment_values_dict():
    class ModelOne(BaseModel):
        a: int

    class ModelTwo(BaseModel):
        m: ModelOne
        b: int

        @validator('b')
        def validate_b(cls, b, values):
            if 'm' in values:
                return b + values['m'].a  # this fails if values['m'] is a dict
            else:
                return b

        class Config:
            validate_assignment = True

    model = ModelTwo(m=ModelOne(a=1), b=2)
    assert model.b == 3
    model.b = 3
    assert model.b == 4


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
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'a is too short', 'type': 'type_error'},
        {'loc': ('b',), 'msg': 'b is too short', 'type': 'type_error'},
    ]


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
    with pytest.raises(errors.ConfigError) as exc_info:

        class Model(BaseModel):
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
        '"tests.test_validators.test_duplicates.<locals>.Model.duplicate_name"; '
        'if this is intended, set `allow_reuse=True`'
    )


def test_use_bare():
    with pytest.raises(errors.ConfigError) as exc_info:

        class Model(BaseModel):
            a: str

            @validator
            def checker(cls, v):
                return v

    assert 'validators should be used with fields' in str(exc_info.value)


def test_use_no_fields():
    with pytest.raises(errors.ConfigError) as exc_info:

        class Model(BaseModel):
            a: str

            @validator()
            def checker(cls, v):
                return v

    assert 'validator with no fields specified' in str(exc_info.value)


def test_validate_always():
    check_calls = 0

    class Model(BaseModel):
        a: str = None

        @validator('a', pre=True, always=True)
        def check_a(cls, v):
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
        @validator('a', pre=True, always=True)
        def check_a(cls, v):
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
        a: str = None

        @validator('a', pre=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or 'xxx'

    assert Model().a is None
    assert check_calls == 0
    assert Model(a='y').a == 'y'
    assert check_calls == 1


def test_wildcard_validators():
    calls = []

    class Model(BaseModel):
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

    assert Model(a='abc', b='123').dict() == dict(a='abc', b=123)
    assert calls == [('check_a', 'abc', 'a'), ('check_all', 'abc', 'a'), ('check_all', 123, 'b')]


def test_wildcard_validator_error():
    class Model(BaseModel):
        a: str
        b: str

        @validator('*')
        def check_all(cls, v, field, **kwargs):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Model(a='foobar a', b='foobar b').b == 'foobar b'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': '"foobar" not found in a', 'type': 'value_error'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_invalid_field():
    with pytest.raises(errors.ConfigError) as exc_info:

        class Model(BaseModel):
            a: str

            @validator('b')
            def check_b(cls, v):
                return v

    assert str(exc_info.value) == (
        "Validators defined with incorrect fields: check_b "  # noqa: Q000
        "(use check_fields=False if you're inheriting from the model and intended this)"
    )


def test_validate_child():
    class Parent(BaseModel):
        a: str

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
    class Parent(BaseModel):
        a: str

        @validator('a')
        def check_a_one(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    class Child(Parent):
        @validator('a')
        def check_a_two(cls, v):
            return v.upper()

    assert Parent(a='this is foobar good').a == 'this is foobar good'
    assert Child(a='this is foobar good').a == 'THIS IS FOOBAR GOOD'
    with pytest.raises(ValidationError):
        Child(a='snap')


def test_validate_child_all():
    class Parent(BaseModel):
        a: str

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
    class Parent(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
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
    class Parent(BaseModel):
        a: str

        @validator('*')
        def check_a(cls, v):
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

        @validator('a')
        def add_to_a(cls, v):
            return v + 1

    class Child(Parent):
        pass

    assert Child(a=0).a == 1


def test_inheritance_replace():
    class Parent(BaseModel):
        a: int

        @validator('a')
        def add_to_a(cls, v):
            return v + 1

    class Child(Parent):
        @validator('a')
        def add_to_a(cls, v):
            return v + 5

    assert Child(a=0).a == 5


def test_inheritance_new():
    class Parent(BaseModel):
        a: int

        @validator('a')
        def add_one_to_a(cls, v):
            return v + 1

    class Child(Parent):
        @validator('a')
        def add_five_to_a(cls, v):
            return v + 5

    assert Child(a=0).a == 6


def test_validation_each_item():
    class Model(BaseModel):
        foobar: Dict[int, int]

        @validator('foobar', each_item=True)
        def check_foobar(cls, v):
            return v + 1

    assert Model(foobar={1: 1}).foobar == {1: 2}


def test_validation_each_item_one_sublevel():
    class Model(BaseModel):
        foobar: List[Tuple[int, int]]

        @validator('foobar', each_item=True)
        def check_foobar(cls, v: Tuple[int, int]) -> Tuple[int, int]:
            v1, v2 = v
            assert v1 == v2
            return v

    assert Model(foobar=[(1, 1), (2, 2)]).foobar == [(1, 1), (2, 2)]


def test_key_validation():
    class Model(BaseModel):
        foobar: Dict[int, int]

        @validator('foobar')
        def check_foobar(cls, value):
            return {k + 1: v + 1 for k, v in value.items()}

    assert Model(foobar={1: 1}).foobar == {2: 2}


def test_validator_always_optional():
    check_calls = 0

    class Model(BaseModel):
        a: Optional[str] = None

        @validator('a', pre=True, always=True)
        def check_a(cls, v):
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

        @validator('a', always=True, pre=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'
    assert check_calls == 2


def test_validator_always_post():
    class Model(BaseModel):
        a: str = None

        @validator('a', always=True)
        def check_a(cls, v):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_validator_always_post_optional():
    class Model(BaseModel):
        a: Optional[str] = None

        @validator('a', always=True, pre=True)
        def check_a(cls, v):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


def test_validator_bad_fields_throws_configerror():
    """
    Attempts to create a validator with fields set as a list of strings,
    rather than just multiple string args. Expects ConfigError to be raised.
    """
    with pytest.raises(ConfigError, match='validator fields should be passed as separate string args.'):

        class Model(BaseModel):
            a: str
            b: str

            @validator(['a', 'b'])
            def check_fields(cls, v):
                return v


def test_datetime_validator():
    check_calls = 0

    class Model(BaseModel):
        d: datetime = None

        @validator('d', pre=True, always=True)
        def check_d(cls, v):
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

        @validator('a', pre=True)
        def check_a(cls, v):
            nonlocal check_calls
            check_calls += 1
            return v

    assert Model(a=['1', '2', '3']).a == (1, 2, 3)
    assert check_calls == 1


@pytest.mark.parametrize(
    'fields,result',
    [
        (['val'], '_v_'),
        (['foobar'], '_v_'),
        (['val', 'field'], '_v_,_field_'),
        (['val', 'config'], '_v_,_config_'),
        (['val', 'values'], '_v_,_values_'),
        (['val', 'field', 'config'], '_v_,_field_,_config_'),
        (['val', 'field', 'values'], '_v_,_field_,_values_'),
        (['val', 'config', 'values'], '_v_,_config_,_values_'),
        (['val', 'field', 'values', 'config'], '_v_,_field_,_values_,_config_'),
        (['cls', 'val'], '_cls_,_v_'),
        (['cls', 'foobar'], '_cls_,_v_'),
        (['cls', 'val', 'field'], '_cls_,_v_,_field_'),
        (['cls', 'val', 'config'], '_cls_,_v_,_config_'),
        (['cls', 'val', 'values'], '_cls_,_v_,_values_'),
        (['cls', 'val', 'field', 'config'], '_cls_,_v_,_field_,_config_'),
        (['cls', 'val', 'field', 'values'], '_cls_,_v_,_field_,_values_'),
        (['cls', 'val', 'config', 'values'], '_cls_,_v_,_config_,_values_'),
        (['cls', 'val', 'field', 'values', 'config'], '_cls_,_v_,_field_,_values_,_config_'),
    ],
)
def test_make_generic_validator(fields, result):
    exec(f"""def testing_function({', '.join(fields)}): return {' + "," + '.join(fields)}""")
    func = locals()['testing_function']
    validator = make_generic_validator(func)
    assert validator.__qualname__ == 'testing_function'
    assert validator.__name__ == 'testing_function'
    # args: cls, v, values, field, config
    assert validator('_cls_', '_v_', '_values_', '_field_', '_config_') == result


def test_make_generic_validator_kwargs():
    def test_validator(v, **kwargs):
        return ', '.join(f'{k}: {v}' for k, v in kwargs.items())

    validator = make_generic_validator(test_validator)
    assert validator.__name__ == 'test_validator'
    assert validator('_cls_', '_v_', '_vs_', '_f_', '_c_') == 'values: _vs_, field: _f_, config: _c_'


def test_make_generic_validator_invalid():
    def test_validator(v, foobar):
        return foobar

    with pytest.raises(ConfigError) as exc_info:
        make_generic_validator(test_validator)
    assert ': (v, foobar), should be: (value, values, config, field)' in str(exc_info.value)


def test_make_generic_validator_cls_kwargs():
    def test_validator(cls, v, **kwargs):
        return ', '.join(f'{k}: {v}' for k, v in kwargs.items())

    validator = make_generic_validator(test_validator)
    assert validator.__name__ == 'test_validator'
    assert validator('_cls_', '_v_', '_vs_', '_f_', '_c_') == 'values: _vs_, field: _f_, config: _c_'


def test_make_generic_validator_cls_invalid():
    def test_validator(cls, v, foobar):
        return foobar

    with pytest.raises(ConfigError) as exc_info:
        make_generic_validator(test_validator)
    assert ': (cls, v, foobar), should be: (cls, value, values, config, field)' in str(exc_info.value)


def test_make_generic_validator_self():
    def test_validator(self, v):
        return v

    with pytest.raises(ConfigError) as exc_info:
        make_generic_validator(test_validator)
    assert ': (self, v), "self" not permitted as first argument, should be: (cls, value' in str(exc_info.value)


def test_assert_raises_validation_error():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            assert v == 'a', 'invalid a'
            return v

    Model(a='a')

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    injected_by_pytest = "\nassert 'snap' == 'a'\n  - a\n  + snap"
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': f'invalid a{injected_by_pytest}', 'type': 'assertion_error'}
    ]


def test_whole():
    with pytest.warns(DeprecationWarning, match='The "whole" keyword argument is deprecated'):

        class Model(BaseModel):
            x: List[int]

            @validator('x', whole=True)
            def check_something(cls, v):
                return v


def test_root_validator():
    root_val_values = []

    class Model(BaseModel):
        a: int = 1
        b: str
        c: str

        @validator('b')
        def repeat_b(cls, v):
            return v * 2

        @root_validator
        def example_root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

        @root_validator
        def example_root_validator2(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('c', ''):
                raise ValueError('foobar2')
            return dict(values, c='changed')

    assert Model(a='123', b='bar', c='baz').dict() == {'a': 123, 'b': 'changed', 'c': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon', c='snap dragon2')
    assert exc_info.value.errors() == [
        {'loc': ('__root__',), 'msg': 'foobar', 'type': 'value_error'},
        {'loc': ('__root__',), 'msg': 'foobar2', 'type': 'value_error'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='broken', b='bar', c='baz')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    assert root_val_values == [
        {'a': 123, 'b': 'barbar', 'c': 'baz'},
        {'a': 123, 'b': 'changed', 'c': 'baz'},
        {'a': 1, 'b': 'snap dragonsnap dragon', 'c': 'snap dragon2'},
        {'a': 1, 'b': 'snap dragonsnap dragon', 'c': 'snap dragon2'},
        {'b': 'barbar', 'c': 'baz'},
        {'b': 'changed', 'c': 'baz'},
    ]


def test_root_validator_pre():
    root_val_values = []

    class Model(BaseModel):
        a: int = 1
        b: str

        @validator('b')
        def repeat_b(cls, v):
            return v * 2

        @root_validator(pre=True)
        def root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return {'a': 42, 'b': 'changed'}

    assert Model(a='123', b='bar').dict() == {'a': 42, 'b': 'changedchanged'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon')

    assert root_val_values == [{'a': '123', 'b': 'bar'}, {'b': 'snap dragon'}]
    assert exc_info.value.errors() == [{'loc': ('__root__',), 'msg': 'foobar', 'type': 'value_error'}]


def test_root_validator_repeat():
    with pytest.raises(errors.ConfigError, match='duplicate validator function'):

        class Model(BaseModel):
            a: int = 1

            @root_validator
            def root_validator_repeated(cls, values):
                return values

            @root_validator  # noqa: F811
            def root_validator_repeated(cls, values):  # noqa: F811
                return values


def test_root_validator_repeat2():
    with pytest.raises(errors.ConfigError, match='duplicate validator function'):

        class Model(BaseModel):
            a: int = 1

            @validator('a')
            def repeat_validator(cls, v):
                return v

            @root_validator(pre=True)  # noqa: F811
            def repeat_validator(cls, values):  # noqa: F811
                return values


def test_root_validator_self():
    with pytest.raises(
        errors.ConfigError, match=r'Invalid signature for root validator root_validator: \(self, values\)'
    ):

        class Model(BaseModel):
            a: int = 1

            @root_validator
            def root_validator(self, values):
                return values


def test_root_validator_extra():
    with pytest.raises(errors.ConfigError) as exc_info:

        class Model(BaseModel):
            a: int = 1

            @root_validator
            def root_validator(cls, values, another):
                return values

    assert str(exc_info.value) == (
        'Invalid signature for root validator root_validator: (cls, values, another), should be: (cls, values).'
    )


def test_root_validator_types():
    root_val_values = None

    class Model(BaseModel):
        a: int = 1
        b: str

        @root_validator
        def root_validator(cls, values):
            nonlocal root_val_values
            root_val_values = cls, values
            return values

        class Config:
            extra = Extra.allow

    assert Model(b='bar', c='wobble').dict() == {'a': 1, 'b': 'bar', 'c': 'wobble'}

    assert root_val_values == (Model, {'a': 1, 'b': 'bar', 'c': 'wobble'})


def test_root_validator_inheritance():
    calls = []

    class Parent(BaseModel):
        pass

        @root_validator
        def root_validator_parent(cls, values):
            calls.append(f'parent validator: {values}')
            return {'extra1': 1, **values}

    class Child(Parent):
        a: int

        @root_validator
        def root_validator_child(cls, values):
            calls.append(f'child validator: {values}')
            return {'extra2': 2, **values}

    assert len(Child.__post_root_validators__) == 2
    assert len(Child.__pre_root_validators__) == 0
    assert Child(a=123).dict() == {'extra2': 2, 'extra1': 1, 'a': 123}
    assert calls == ["parent validator: {'a': 123}", "child validator: {'extra1': 1, 'a': 123}"]


def test_root_validator_returns_none_exception():
    class Model(BaseModel):
        a: int = 1

        @root_validator
        def root_validator_repeated(cls, values):
            return None

    with pytest.raises(TypeError, match='Model values must be a dict'):
        Model()


def reusable_validator(num):
    return num * 2


def test_reuse_global_validators():
    class Model(BaseModel):
        x: int
        y: int

        double_x = validator('x', allow_reuse=True)(reusable_validator)
        double_y = validator('y', allow_reuse=True)(reusable_validator)

    assert dict(Model(x=1, y=1)) == {'x': 2, 'y': 2}


def declare_with_reused_validators(include_root, allow_1, allow_2, allow_3):
    class Model(BaseModel):
        a: str
        b: str

        @validator('a', allow_reuse=allow_1)
        def duplicate_name(cls, v):
            return v

        @validator('b', allow_reuse=allow_2)  # noqa F811
        def duplicate_name(cls, v):  # noqa F811
            return v

        if include_root:

            @root_validator(allow_reuse=allow_3)  # noqa F811
            def duplicate_name(cls, values):  # noqa F811
                return values


@pytest.fixture
def reset_tracked_validators():
    from pydantic.class_validators import _FUNCS

    original_tracked_validators = set(_FUNCS)
    yield
    _FUNCS.clear()
    _FUNCS.update(original_tracked_validators)


@pytest.mark.parametrize('include_root,allow_1,allow_2,allow_3', product(*[[True, False]] * 4))
def test_allow_reuse(include_root, allow_1, allow_2, allow_3, reset_tracked_validators):
    duplication_count = int(not allow_1) + int(not allow_2) + int(include_root and not allow_3)
    if duplication_count > 1:
        with pytest.raises(ConfigError) as exc_info:
            declare_with_reused_validators(include_root, allow_1, allow_2, allow_3)
        assert str(exc_info.value).startswith('duplicate validator function')
    else:
        declare_with_reused_validators(include_root, allow_1, allow_2, allow_3)


@pytest.mark.parametrize('validator_classmethod,root_validator_classmethod', product(*[[True, False]] * 2))
def test_root_validator_classmethod(validator_classmethod, root_validator_classmethod, reset_tracked_validators):
    root_val_values = []

    class Model(BaseModel):
        a: int = 1
        b: str

        def repeat_b(cls, v):
            return v * 2

        if validator_classmethod:
            repeat_b = classmethod(repeat_b)
        repeat_b = validator('b')(repeat_b)

        def example_root_validator(cls, values):
            root_val_values.append(values)
            if 'snap' in values.get('b', ''):
                raise ValueError('foobar')
            return dict(values, b='changed')

        if root_validator_classmethod:
            example_root_validator = classmethod(example_root_validator)
        example_root_validator = root_validator(example_root_validator)

    assert Model(a='123', b='bar').dict() == {'a': 123, 'b': 'changed'}

    with pytest.raises(ValidationError) as exc_info:
        Model(b='snap dragon')
    assert exc_info.value.errors() == [{'loc': ('__root__',), 'msg': 'foobar', 'type': 'value_error'}]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='broken', b='bar')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    assert root_val_values == [{'a': 123, 'b': 'barbar'}, {'a': 1, 'b': 'snap dragonsnap dragon'}, {'b': 'barbar'}]


def test_root_validator_skip_on_failure():
    a_called = False

    class ModelA(BaseModel):
        a: int

        @root_validator
        def example_root_validator(cls, values):
            nonlocal a_called
            a_called = True

    with pytest.raises(ValidationError):
        ModelA(a='a')
    assert a_called
    b_called = False

    class ModelB(BaseModel):
        a: int

        @root_validator(skip_on_failure=True)
        def example_root_validator(cls, values):
            nonlocal b_called
            b_called = True

    with pytest.raises(ValidationError):
        ModelB(a='a')
    assert not b_called


def test_assignment_validator_cls():
    validator_calls = 0

    class Model(BaseModel):
        name: str

        class Config:
            validate_assignment = True

        @validator('name')
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
            'loc': ('a',),
            'msg': "unexpected value; permitted: 'foo'",
            'type': 'value_error.const',
            'ctx': {'given': 'nope', 'permitted': ('foo',)},
        }
    ]


def test_literal_validator_str_enum():
    class Bar(str, Enum):
        FIZ = 'fiz'
        FUZ = 'fuz'

    class Foo(BaseModel):
        bar: Bar
        barfiz: Literal[Bar.FIZ]
        fizfuz: Literal[Bar.FIZ, Bar.FUZ]

    my_foo = Foo.parse_obj({'bar': 'fiz', 'barfiz': 'fiz', 'fizfuz': 'fiz'})
    assert my_foo.bar is Bar.FIZ
    assert my_foo.barfiz is Bar.FIZ
    assert my_foo.fizfuz is Bar.FIZ

    my_foo = Foo.parse_obj({'bar': 'fiz', 'barfiz': 'fiz', 'fizfuz': 'fuz'})
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
            'loc': ('a',),
            'msg': "unexpected value; permitted: 'foo', 'bar'",
            'type': 'value_error.const',
            'ctx': {'given': 'nope', 'permitted': ('foo', 'bar')},
        }
    ]


def test_union_literal_with_constraints():
    class Model(BaseModel, validate_assignment=True):
        x: Union[Literal[42], Literal['pika']] = Field(allow_mutation=False)

    m = Model(x=42)
    with pytest.raises(TypeError):
        m.x += 1


def test_field_that_is_being_validated_is_excluded_from_validator_values(mocker):
    check_values = mocker.MagicMock()

    class Model(BaseModel):
        foo: str
        bar: str = Field(alias='pika')
        baz: str

        class Config:
            validate_assignment = True

        @validator('foo')
        def validate_foo(cls, v, values):
            check_values({**values})
            return v

        @validator('bar')
        def validate_bar(cls, v, values):
            check_values({**values})
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

        class Config:
            validate_assignment = True

        @validator('foo')
        def validate_foo(cls, v):
            if v == 'raise_exception':
                raise RuntimeError('test error')
            return v

    model = Model(foo='foo')
    with pytest.raises(RuntimeError, match='test error'):
        model.foo = 'raise_exception'
    assert model.foo == 'foo'


def test_overridden_root_validators(mocker):
    validate_stub = mocker.stub(name='validate')

    class A(BaseModel):
        x: str

        @root_validator(pre=True)
        def pre_root(cls, values):
            validate_stub('A', 'pre')
            return values

        @root_validator(pre=False)
        def post_root(cls, values):
            validate_stub('A', 'post')
            return values

    class B(A):
        @root_validator(pre=True)
        def pre_root(cls, values):
            validate_stub('B', 'pre')
            return values

        @root_validator(pre=False)
        def post_root(cls, values):
            validate_stub('B', 'post')
            return values

    A(x='pika')
    assert validate_stub.call_args_list == [mocker.call('A', 'pre'), mocker.call('A', 'post')]

    validate_stub.reset_mock()

    B(x='pika')
    assert validate_stub.call_args_list == [mocker.call('B', 'pre'), mocker.call('B', 'post')]


def test_list_unique_items_with_optional():
    class Model(BaseModel):
        foo: Optional[List[str]] = Field(None, unique_items=True)
        bar: conlist(str, unique_items=True) = Field(None)

    assert Model().dict() == {'foo': None, 'bar': None}
    assert Model(foo=None, bar=None).dict() == {'foo': None, 'bar': None}
    assert Model(foo=['k1'], bar=['k1']).dict() == {'foo': ['k1'], 'bar': ['k1']}
    with pytest.raises(ValidationError) as exc_info:
        Model(foo=['k1', 'k1'], bar=['k1', 'k1'])
    assert exc_info.value.errors() == [
        {'loc': ('foo',), 'msg': 'the list has duplicated items', 'type': 'value_error.list.unique_items'},
        {'loc': ('bar',), 'msg': 'the list has duplicated items', 'type': 'value_error.list.unique_items'},
    ]


@pytest.mark.parametrize(
    'func,allow_reuse',
    [
        pytest.param(partial, False, id='`partial` and check for reuse'),
        pytest.param(partial, True, id='`partial` and ignore reuse'),
        pytest.param(partialmethod, False, id='`partialmethod` and check for reuse'),
        pytest.param(partialmethod, True, id='`partialmethod` and ignore reuse'),
    ],
)
def test_functool_as_validator(
    reset_tracked_validators,
    func: Callable,
    allow_reuse: bool,
):
    def custom_validator(
        cls,
        v: Any,
        allowed: str,
    ) -> Any:
        assert v == allowed, f'Only {allowed} allowed as value; given: {v}'
        return v

    validate = func(custom_validator, allowed='TEXT')

    class TestClass(BaseModel):
        name: str
        _custom_validate = validator('name', allow_reuse=allow_reuse)(validate)
