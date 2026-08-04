from decimal import Decimal
from typing import Annotated

import annotated_types
import pytest

from pydantic import (
    BaseModel,
    NegativeInt,
    NonNegativeInt,
    NonPositiveInt,
    PositiveInt,
    StrictInt,
    TypeAdapter,
    ValidationError,
)


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param(1, 1, id='1_int'),
        (1.0, 1),
        (1.9, ValidationError),
        (Decimal(1), 1),
        (Decimal(1.9), ValidationError),
        pytest.param('1', 1, id='1_str'),
        pytest.param('1.9', ValidationError, id='1.9_str'),
        (b'1', 1),
        pytest.param(12, 12, id='12_int'),
        pytest.param('12', 12, id='12_str'),
        pytest.param(b'12', 12, id='12_bytes'),
    ],
)
def test_int_coercions(value, expected):
    class Model(BaseModel):
        v: int

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_int_validation():
    class Model(BaseModel):
        a: PositiveInt = None
        b: NegativeInt = None
        c: NonNegativeInt = None
        d: NonPositiveInt = None
        e: Annotated[int, annotated_types.Interval(gt=4, lt=10)] = None
        f: Annotated[int, annotated_types.Interval(ge=0, le=10)] = None
        g: Annotated[int, annotated_types.MultipleOf(5)] = None

    m = Model(a=5, b=-5, c=0, d=0, e=5, f=0, g=25)
    assert m.model_dump() == {'a': 5, 'b': -5, 'c': 0, 'd': 0, 'e': 5, 'f': 0, 'g': 25}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5, b=5, c=-5, d=5, e=-5, f=11, g=42)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than 0',
            'input': -5,
            'ctx': {'gt': 0},
        },
        {
            'type': 'less_than',
            'loc': ('b',),
            'msg': 'Input should be less than 0',
            'input': 5,
            'ctx': {'lt': 0},
        },
        {
            'type': 'greater_than_equal',
            'loc': ('c',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -5,
            'ctx': {'ge': 0},
        },
        {
            'type': 'less_than_equal',
            'loc': ('d',),
            'msg': 'Input should be less than or equal to 0',
            'input': 5,
            'ctx': {'le': 0},
        },
        {
            'type': 'greater_than',
            'loc': ('e',),
            'msg': 'Input should be greater than 4',
            'input': -5,
            'ctx': {'gt': 4},
        },
        {
            'type': 'less_than_equal',
            'loc': ('f',),
            'msg': 'Input should be less than or equal to 10',
            'input': 11,
            'ctx': {'le': 10},
        },
        {
            'type': 'multiple_of',
            'loc': ('g',),
            'msg': 'Input should be a multiple of 5',
            'input': 42,
            'ctx': {'multiple_of': 5},
        },
    ]


def test_strict_int():
    class Model(BaseModel):
        v: StrictInt

    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v='123456')

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v=3.14159)

    with pytest.raises(ValidationError, match=r'Input should be a valid integer \[type=int_type,'):
        Model(v=True)


@pytest.mark.parametrize(
    ('input', 'expected_json'),
    (
        (9_223_372_036_854_775_807, b'9223372036854775807'),
        (-9_223_372_036_854_775_807, b'-9223372036854775807'),
        (1433352099889938534014333520998899385340, b'1433352099889938534014333520998899385340'),
        (-1433352099889938534014333520998899385340, b'-1433352099889938534014333520998899385340'),
    ),
)
def test_big_int_json(input, expected_json):
    v = TypeAdapter(int)
    dumped = v.dump_json(input)
    assert dumped == expected_json
    assert v.validate_json(dumped) == input


def test_number_gt():
    class Model(BaseModel):
        a: Annotated[int, annotated_types.Gt(-1)] = 0

    assert Model(a=0).model_dump() == {'a': 0}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('a',),
            'msg': 'Input should be greater than -1',
            'input': -1,
            'ctx': {'gt': -1},
        }
    ]


def test_number_ge():
    class Model(BaseModel):
        a: Annotated[int, annotated_types.Ge(0)] = 0

    assert Model(a=0).model_dump() == {'a': 0}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than_equal',
            'loc': ('a',),
            'msg': 'Input should be greater than or equal to 0',
            'input': -1,
            'ctx': {'ge': 0},
        }
    ]


def test_number_lt():
    class Model(BaseModel):
        a: Annotated[int, annotated_types.Lt(5)] = 0

    assert Model(a=4).model_dump() == {'a': 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=5)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'less_than',
            'loc': ('a',),
            'msg': 'Input should be less than 5',
            'input': 5,
            'ctx': {'lt': 5},
        }
    ]


def test_number_le():
    class Model(BaseModel):
        a: Annotated[int, annotated_types.Le(5)] = 0

    assert Model(a=5).model_dump() == {'a': 5}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=6)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'less_than_equal',
            'loc': ('a',),
            'msg': 'Input should be less than or equal to 5',
            'input': 6,
            'ctx': {'le': 5},
        }
    ]


@pytest.mark.parametrize('value', (10, 100, 20))
def test_number_multiple_of_int_valid(value):
    class Model(BaseModel):
        a: Annotated[int, annotated_types.MultipleOf(5)]

    assert Model(a=value).model_dump() == {'a': value}


@pytest.mark.parametrize('value', [1337, 23, 6, 14])
def test_number_multiple_of_int_invalid(value):
    class Model(BaseModel):
        a: Annotated[int, annotated_types.MultipleOf(5)]

    with pytest.raises(ValidationError) as exc_info:
        Model(a=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_of',
            'loc': ('a',),
            'msg': 'Input should be a multiple of 5',
            'input': value,
            'ctx': {'multiple_of': 5},
        }
    ]
