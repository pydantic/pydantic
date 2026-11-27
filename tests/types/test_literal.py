import typing
from decimal import Decimal
from enum import Enum, IntEnum
from fractions import Fraction
from typing import Any, Literal

import pytest
import typing_extensions

from pydantic import TypeAdapter, ValidationError


def test_literal_single():
    ta = TypeAdapter(Literal['a'])

    assert ta.validate_python('a') == 'a'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('b')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a'",
            'input': 'b',
            'ctx': {'expected': "'a'"},
        }
    ]


def test_literal_multiple():
    ta = TypeAdapter(Literal['a', 'b'])

    assert ta.validate_python('a') == 'a'
    assert ta.validate_python('b') == 'b'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        }
    ]


@pytest.mark.parametrize(
    'typing_literal',
    [
        pytest.param(typing.Literal, id='typing.Literal'),
        pytest.param(typing_extensions.Literal, id='typing_extensions.Literal'),
    ],
)
def test_literal_field(typing_literal):
    ta = TypeAdapter(typing_literal['foo'])

    assert ta.validate_python('foo') == 'foo'


class IntE(IntEnum):
    a = 2


class StrE(str, Enum):
    a = 'a'


@pytest.mark.parametrize(
    ['tp', 'value', 'expected'],
    [
        pytest.param(Literal[2], 2, 2, id='int'),
        pytest.param(Literal[2], IntE.a, 2, id='int_enum'),
        pytest.param(Literal['a'], StrE.a, 'a', id='str_enum'),
        pytest.param(Literal[2**70], 2**70, 2**70, id='big_int'),
        pytest.param(Literal[2**70, 1], 2**70, 2**70, id='big_int_with_small_int'),
        pytest.param(Literal[True], True, True, id='bool'),
    ],
)
def test_literal_python_valid(tp: Any, value: Any, expected: Any) -> None:
    assert TypeAdapter(tp).validate_python(value) == expected


@pytest.mark.parametrize(
    ['tp', 'value'],
    [
        pytest.param(Literal[2], 2.0, id='float_for_int'),
        pytest.param(Literal[2], Decimal(2), id='decimal_for_int'),
        pytest.param(Literal[2], Fraction(2), id='fraction_for_int'),
        pytest.param(Literal[2**70], float(2**70), id='float_for_big_int'),
        pytest.param(Literal[1], True, id='true_for_int'),
        pytest.param(Literal[0], False, id='false_for_int'),
        pytest.param(Literal[True], 1, id='int_for_true'),
        pytest.param(Literal[True], 1.0, id='float_for_true'),
        pytest.param(Literal[False], 0, id='int_for_false'),
    ],
)
def test_literal_python_invalid(tp: Any, value: Any) -> None:
    """https://github.com/pydantic/pydantic/issues/14066"""

    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(tp).validate_python(value)
    assert exc_info.value.errors()[0]['type'] == 'literal_error'


@pytest.mark.parametrize(
    ['tp', 'value'],
    [
        pytest.param(Literal[2], '2.0', id='float_for_int'),
        pytest.param(Literal[2], '2e0', id='exponent_float_for_int'),
        pytest.param(Literal[1], 'true', id='true_for_int'),
        pytest.param(Literal[True], '1', id='int_for_true'),
    ],
)
def test_literal_json_invalid(tp: Any, value: str) -> None:
    """https://github.com/pydantic/pydantic/issues/14066"""

    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(tp).validate_json(value)
    assert exc_info.value.errors()[0]['type'] == 'literal_error'
