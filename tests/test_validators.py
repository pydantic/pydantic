from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytest

from pydantic import BaseModel, ConfigError, ValidationError, errors, validator
from pydantic.class_validators import make_generic_validator


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
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


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
        'duplicate validator function ' '"tests.test_validators.test_duplicates.<locals>.Model.duplicate_name"'
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
        "Validators defined with incorrect fields: check_b "
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


def test_no_key_validation():
    class Model(BaseModel):
        foobar: Dict[int, int]

        @validator('foobar')
        def check_foobar(cls, v):
            return v + 1

    assert Model(foobar={1: 1}).foobar == {1: 2}


def test_key_validation_whole():
    class Model(BaseModel):
        foobar: Dict[int, int]

        @validator('foobar', whole=True)
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


def test_validator_always_post():
    class Model(BaseModel):
        a: str = None

        @validator('a', always=True)
        def check_a(cls, v):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    with pytest.raises(ValidationError):
        Model()


def test_validator_always_post_optional():
    class Model(BaseModel):
        a: Optional[str] = None

        @validator('a', always=True)
        def check_a(cls, v):
            return v or 'default value'

    assert Model(a='y').a == 'y'
    assert Model().a == 'default value'


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


def test_whole_called_once():
    check_calls = 0

    class Model(BaseModel):
        a: Tuple[int, int, int]

        @validator('a', pre=True, whole=True)
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
