import json
import math
from decimal import Decimal
from typing import Annotated

import annotated_types
import pytest
from dirty_equals import HasRepr, IsFloatNan

from pydantic import (
    AllowInfNan,
    BaseModel,
    ConfigDict,
    FiniteFloat,
    NegativeFloat,
    NonNegativeFloat,
    NonPositiveFloat,
    PositiveFloat,
    StrictFloat,
    ValidationError,
)


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param(1, 1.0, id='1_int'),
        pytest.param(1.0, 1.0, id='1.0_float'),
        (Decimal(1.0), 1.0),
        pytest.param('1.0', 1.0, id='1.0_str'),
        pytest.param('1', 1.0, id='1_str'),
        pytest.param(b'1.0', 1.0, id='1.0_bytes'),
        pytest.param(b'1', 1.0, id='1_bytes'),
        (True, 1.0),
        (False, 0.0),
        pytest.param('t', ValidationError, id='t_str'),
        pytest.param(b't', ValidationError, id='t_bytes'),
    ],
)
def test_float_coercions(value, expected):
    class Model(BaseModel):
        v: float

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_float_validation():
    class Model(BaseModel):
        a: PositiveFloat = None
        b: NegativeFloat = None
        c: NonNegativeFloat = None
        d: NonPositiveFloat = None
        e: Annotated[float, annotated_types.Interval(gt=4, lt=12.2)] = None
        f: Annotated[float, annotated_types.Interval(ge=0, le=9.9)] = None
        g: Annotated[float, annotated_types.MultipleOf(0.5)] = None
        h: Annotated[float, AllowInfNan(False)] = None

    m = Model(a=5.1, b=-5.2, c=0, d=0, e=5.3, f=9.9, g=2.5, h=42)
    assert m.model_dump() == {'a': 5.1, 'b': -5.2, 'c': 0, 'd': 0, 'e': 5.3, 'f': 9.9, 'g': 2.5, 'h': 42}

    assert Model(a=float('inf')).a == float('inf')
    assert Model(b=float('-inf')).b == float('-inf')

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5.1, b=5.2, c=-5.1, d=5.1, e=-5.3, f=9.91, g=4.2, h=float('nan'))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than 0',
            'input': -5.1,
            'ctx': {
                'gt': 0.0,
            },
        },
        {
            'type': 'less_than',
            'loc': ('b',),
            'msg': 'Input should be less than 0',
            'input': 5.2,
            'ctx': {
                'lt': 0.0,
            },
        },
        {
            'type': 'greater_than_equal',
            'loc': ('c',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -5.1,
            'ctx': {
                'ge': 0.0,
            },
        },
        {
            'type': 'less_than_equal',
            'loc': ('d',),
            'msg': 'Input should be less than or equal to 0',
            'input': 5.1,
            'ctx': {
                'le': 0.0,
            },
        },
        {
            'type': 'greater_than',
            'loc': ('e',),
            'msg': 'Input should be greater than 4',
            'input': -5.3,
            'ctx': {
                'gt': 4.0,
            },
        },
        {
            'type': 'less_than_equal',
            'loc': ('f',),
            'msg': 'Input should be less than or equal to 9.9',
            'input': 9.91,
            'ctx': {
                'le': 9.9,
            },
        },
        {
            'type': 'multiple_of',
            'loc': ('g',),
            'msg': 'Input should be a multiple of 0.5',
            'input': 4.2,
            'ctx': {
                'multiple_of': 0.5,
            },
        },
        {
            'type': 'finite_number',
            'loc': ('h',),
            'msg': 'Input should be a finite number',
            'input': HasRepr('nan'),
        },
    ]


def test_infinite_float_validation():
    class Model(BaseModel):
        a: float = None

    assert Model(a=float('inf')).a == float('inf')
    assert Model(a=float('-inf')).a == float('-inf')
    assert math.isnan(Model(a=float('nan')).a)


@pytest.mark.parametrize(
    ('ser_json_inf_nan', 'input', 'output', 'python_roundtrip'),
    (
        ('null', float('inf'), 'null', None),
        ('null', float('-inf'), 'null', None),
        ('null', float('nan'), 'null', None),
        ('constants', float('inf'), 'Infinity', float('inf')),
        ('constants', float('-inf'), '-Infinity', float('-inf')),
        ('constants', float('nan'), 'NaN', IsFloatNan),
    ),
)
def test_infinite_float_json_serialization(ser_json_inf_nan, input, output, python_roundtrip):
    class Model(BaseModel):
        model_config = ConfigDict(ser_json_inf_nan=ser_json_inf_nan)
        a: float

    json_string = Model(a=input).model_dump_json()
    assert json_string == f'{{"a":{output}}}'
    assert json.loads(json_string) == {'a': python_roundtrip}


@pytest.mark.parametrize('value', [float('inf'), float('-inf'), float('nan')])
def test_finite_float_validation_error(value):
    class Model(BaseModel):
        a: FiniteFloat

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'finite_number',
            'loc': ('a',),
            'msg': 'Input should be a finite number',
            'input': HasRepr(repr(value)),
        }
    ]


def test_finite_float_config():
    class Model(BaseModel):
        a: float

        model_config = ConfigDict(allow_inf_nan=False)

    assert Model(a=42).a == 42
    with pytest.raises(ValidationError) as exc_info:
        Model(a=float('nan'))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'finite_number',
            'loc': ('a',),
            'msg': 'Input should be a finite number',
            'input': HasRepr('nan'),
        }
    ]


def test_strict_float():
    class Model(BaseModel):
        v: StrictFloat

    assert Model(v=3.14159).v == 3.14159
    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[type=float_type,'):
        Model(v='3.14159')

    with pytest.raises(ValidationError, match=r'Input should be a valid number \[type=float_type,'):
        Model(v=True)


@pytest.mark.parametrize('value', [0.2, 0.3, 0.4, 0.5, 1])
def test_number_multiple_of_float_valid(value):
    class Model(BaseModel):
        a: Annotated[float, annotated_types.MultipleOf(0.1)]

    assert Model(a=value).model_dump() == {'a': value}


@pytest.mark.parametrize('value', [0.07, 1.27, 1.003])
def test_number_multiple_of_float_invalid(value):
    class Model(BaseModel):
        a: Annotated[float, annotated_types.MultipleOf(0.1)]

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_of',
            'loc': ('a',),
            'msg': 'Input should be a multiple of 0.1',
            'input': value,
            'ctx': {'multiple_of': 0.1},
        }
    ]
