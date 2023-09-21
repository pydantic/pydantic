from __future__ import annotations

import json
import math
import re
from decimal import Decimal
from typing import Any, Dict

import pytest
from dirty_equals import FunctionCheck, IsStr

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


class DecimalSubclass(Decimal):
    pass


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, Decimal(0)),
        (1, Decimal(1)),
        (42, Decimal(42)),
        ('42', Decimal(42)),
        ('42.123', Decimal('42.123')),
        (42.0, Decimal(42)),
        (42.5, Decimal('42.5')),
        (1e10, Decimal('1E10')),
        (Decimal('42.0'), Decimal(42)),
        (Decimal('42.5'), Decimal('42.5')),
        (Decimal('1e10'), Decimal('1E10')),
        (
            Decimal('123456789123456789123456789.123456789123456789123456789'),
            Decimal('123456789123456789123456789.123456789123456789123456789'),
        ),
        (DecimalSubclass('42.0'), Decimal(42)),
        (DecimalSubclass('42.5'), Decimal('42.5')),
        (DecimalSubclass('1e10'), Decimal('1E10')),
        (
            True,
            Err(
                'Decimal input should be an integer, float, string or Decimal object [type=decimal_type, input_value=True, input_type=bool]'
            ),
        ),
        (
            False,
            Err(
                'Decimal input should be an integer, float, string or Decimal object [type=decimal_type, input_value=False, input_type=bool]'
            ),
        ),
        ('wrong', Err('Input should be a valid decimal [type=decimal_parsing')),
        (
            [1, 2],
            Err(
                'Decimal input should be an integer, float, string or Decimal object [type=decimal_type, input_value=[1, 2], input_type=list]'
            ),
        ),
    ],
)
def test_decimal(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'decimal'})
    # Decimal types are not JSON serializable
    if v.validator_type == 'json' and isinstance(input_value, Decimal):
        input_value = str(input_value)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, Decimal)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Decimal(0), Decimal(0)),
        (Decimal(1), Decimal(1)),
        (Decimal(42), Decimal(42)),
        (Decimal('42.0'), Decimal('42.0')),
        (Decimal('42.5'), Decimal('42.5')),
        (42.0, Err('Input should be an instance of Decimal [type=is_instance_of, input_value=42.0, input_type=float]')),
        ('42', Err("Input should be an instance of Decimal [type=is_instance_of, input_value='42', input_type=str]")),
        (42, Err('Input should be an instance of Decimal [type=is_instance_of, input_value=42, input_type=int]')),
        (True, Err('Input should be an instance of Decimal [type=is_instance_of, input_value=True, input_type=bool]')),
    ],
    ids=repr,
)
def test_decimal_strict_py(input_value, expected):
    v = SchemaValidator({'type': 'decimal', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, Decimal)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, Decimal(0)),
        (1, Decimal(1)),
        (42, Decimal(42)),
        ('42.0', Decimal('42.0')),
        ('42.5', Decimal('42.5')),
        (42.0, Decimal('42.0')),
        ('42', Decimal('42')),
        (
            True,
            Err(
                'Decimal input should be an integer, float, string or Decimal object [type=decimal_type, input_value=True, input_type=bool]'
            ),
        ),
    ],
    ids=repr,
)
def test_decimal_strict_json(input_value, expected):
    v = SchemaValidator({'type': 'decimal', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(json.dumps(input_value))
    else:
        output = v.validate_json(json.dumps(input_value))
        assert output == expected
        assert isinstance(output, Decimal)


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 0, Decimal(0)),
        ({}, '123.456', Decimal('123.456')),
        ({'ge': 0}, 0, Decimal(0)),
        (
            {'ge': 0},
            -0.1,
            Err(
                'Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-0.1, input_type=float]'
            ),
        ),
        ({'gt': 0}, 0.1, Decimal('0.1')),
        ({'gt': 0}, 0, Err('Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]')),
        ({'le': 0}, 0, Decimal(0)),
        ({'le': 0}, -1, Decimal(-1)),
        ({'le': 0}, 0.1, Err('Input should be less than or equal to 0')),
        ({'lt': 0}, 0, Err('Input should be less than 0')),
        ({'lt': 0.123456}, 1, Err('Input should be less than 0.123456')),
    ],
)
def test_decimal_kwargs(py_and_json: PyAndJson, kwargs: Dict[str, Any], input_value, expected):
    v = py_and_json({'type': 'decimal', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, Decimal)


@pytest.mark.parametrize(
    'multiple_of,input_value,error',
    [
        (0.5, 0.5, None),
        (0.5, 1, None),
        (0.5, 0.6, Err('Input should be a multiple of 0.5')),
        (0.5, 0.51, Err('Input should be a multiple of 0.5')),
        (0.5, 0.501, Err('Input should be a multiple of 0.5')),
        (0.5, 1_000_000.5, None),
        (0.5, 1_000_000.49, Err('Input should be a multiple of 0.5')),
        (0.1, 0, None),
        (0.1, 0.0, None),
        (0.1, 0.2, None),
        (0.1, 0.3, None),
        (0.1, 0.4, None),
        (0.1, 0.5, None),
        (0.1, 0.5001, Err('Input should be a multiple of 0.1')),
        (0.1, 1, None),
        (0.1, 1.0, None),
        (0.1, int(5e10), None),
    ],
    ids=repr,
)
def test_decimal_multiple_of(py_and_json: PyAndJson, multiple_of: float, input_value: float, error: Err | None):
    v = py_and_json({'type': 'decimal', 'multiple_of': Decimal(str(multiple_of))})
    if error:
        with pytest.raises(ValidationError, match=re.escape(error.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == Decimal(str(input_value))
        assert isinstance(output, Decimal)


def test_union_decimal_py():
    v = SchemaValidator(
        {'type': 'union', 'choices': [{'type': 'decimal', 'strict': True}, {'type': 'decimal', 'multiple_of': 7}]}
    )
    assert v.validate_python('14') == 14
    assert v.validate_python(Decimal(5)) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('5')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('decimal',),
            'msg': 'Input should be an instance of Decimal',
            'input': '5',
            'ctx': {'class': 'Decimal'},
        },
        {
            'type': 'multiple_of',
            'loc': ('decimal',),
            'msg': 'Input should be a multiple of 7',
            'input': '5',
            'ctx': {'multiple_of': 7},
        },
    ]


def test_union_decimal_json():
    v = SchemaValidator(
        {'type': 'union', 'choices': [{'type': 'decimal', 'strict': True}, {'type': 'decimal', 'multiple_of': 7}]}
    )
    assert v.validate_json(json.dumps('14')) == 14
    assert v.validate_json(json.dumps('5')) == 5


def test_union_decimal_simple(py_and_json: PyAndJson):
    v = py_and_json({'type': 'union', 'choices': [{'type': 'decimal'}, {'type': 'list'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'decimal_parsing', 'loc': ('decimal',), 'msg': 'Input should be a valid decimal', 'input': 'xxx'},
        {
            'type': 'list_type',
            'loc': ('list[any]',),
            'msg': IsStr(regex='Input should be a valid (list|array)'),
            'input': 'xxx',
        },
    ]


def test_decimal_repr():
    v = SchemaValidator({'type': 'decimal'})
    assert plain_repr(v).startswith(
        'SchemaValidator(title="decimal",validator=Decimal(DecimalValidator{strict:false,allow_inf_nan:false'
    )
    v = SchemaValidator({'type': 'decimal', 'strict': True})
    assert plain_repr(v).startswith(
        'SchemaValidator(title="decimal",validator=Decimal(DecimalValidator{strict:true,allow_inf_nan:false'
    )
    v = SchemaValidator({'type': 'decimal', 'multiple_of': 7})
    assert plain_repr(v).startswith('SchemaValidator(title="decimal",validator=Decimal(')


@pytest.mark.parametrize('input_value,expected', [(Decimal('1.23'), Decimal('1.23')), (Decimal('1'), Decimal('1.0'))])
def test_decimal_not_json(input_value, expected):
    v = SchemaValidator({'type': 'decimal'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, Decimal)


def test_decimal_nan(py_and_json: PyAndJson):
    v = py_and_json({'type': 'decimal', 'allow_inf_nan': True})
    assert v.validate_test('inf') == Decimal('inf')
    assert v.validate_test('-inf') == Decimal('-inf')
    r = v.validate_test('nan')
    assert math.isnan(r)


def test_decimal_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'decimal'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 1, '2': 2}) == {Decimal('1'): 1, Decimal('2'): 2}
    assert v.validate_test({'1.5': 1, '2.4': 2}) == {Decimal('1.5'): 1, Decimal('2.4'): 2}
    if v.validator_type == 'python':
        with pytest.raises(ValidationError, match='Input should be an instance of Decimal'):
            v.validate_test({'1.5': 1, '2.5': 2}, strict=True)
    else:
        assert v.validate_test({'1.5': 1, '2.4': 2}, strict=True) == {Decimal('1.5'): 1, Decimal('2.4'): 2}


@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        ('NaN', True, FunctionCheck(math.isnan)),
        ('NaN', False, Err("Input should be a finite number [type=finite_number, input_value='NaN', input_type=str]")),
        ('+inf', True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
        (
            '+inf',
            False,
            Err("Input should be a finite number [type=finite_number, input_value='+inf', input_type=str]"),
        ),
        ('+infinity', True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
        (
            '+infinity',
            False,
            Err("Input should be a finite number [type=finite_number, input_value='+infinity', input_type=str]"),
        ),
        ('-inf', True, FunctionCheck(lambda x: math.isinf(x) and x < 0)),
        (
            '-inf',
            False,
            Err("Input should be a finite number [type=finite_number, input_value='-inf', input_type=str]"),
        ),
        ('-infinity', True, FunctionCheck(lambda x: math.isinf(x) and x < 0)),
        (
            '-infinity',
            False,
            Err("Input should be a finite number [type=finite_number, input_value='-infinity', input_type=str]"),
        ),
        ('0.7', True, Decimal('0.7')),
        ('0.7', False, Decimal('0.7')),
        (
            'pika',
            True,
            Err("Input should be a valid decimal [type=decimal_parsing, input_value='pika', input_type=str]"),
        ),
        (
            'pika',
            False,
            Err("Input should be a valid decimal [type=decimal_parsing, input_value='pika', input_type=str]"),
        ),
    ],
)
def test_non_finite_json_values(py_and_json: PyAndJson, input_value, allow_inf_nan, expected):
    v = py_and_json({'type': 'decimal', 'allow_inf_nan': allow_inf_nan})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('strict', (True, False))
@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        (Decimal('nan'), True, FunctionCheck(math.isnan)),
        (
            Decimal('nan'),
            False,
            Err("Input should be a finite number [type=finite_number, input_value=Decimal('NaN'), input_type=Decimal]"),
        ),
    ],
)
def test_non_finite_decimal_values(strict, input_value, allow_inf_nan, expected):
    v = SchemaValidator({'type': 'decimal', 'allow_inf_nan': allow_inf_nan, 'strict': strict})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        (Decimal('+inf'), True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
        (
            Decimal('+inf'),
            False,
            Err(
                "Input should be a finite number [type=finite_number, input_value=Decimal('Infinity'), input_type=Decimal]"
            ),
        ),
        (
            Decimal('-inf'),
            True,
            Err(
                "Input should be greater than 0 [type=greater_than, input_value=Decimal('-Infinity'), input_type=Decimal]"
            ),
        ),
        (
            Decimal('-inf'),
            False,
            Err(
                "Input should be a finite number [type=finite_number, input_value=Decimal('-Infinity'), input_type=Decimal]"
            ),
        ),
    ],
)
def test_non_finite_constrained_decimal_values(input_value, allow_inf_nan, expected):
    v = SchemaValidator({'type': 'decimal', 'allow_inf_nan': allow_inf_nan, 'gt': 0})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        # lower e, minus
        ('1.0e-12', Decimal('1e-12')),
        ('1e-12', Decimal('1e-12')),
        ('12e-1', Decimal('12e-1')),
        # upper E, minus
        ('1.0E-12', Decimal('1e-12')),
        ('1E-12', Decimal('1e-12')),
        ('12E-1', Decimal('12e-1')),
        # lower E, plus
        ('1.0e+12', Decimal(' 1e12')),
        ('1e+12', Decimal(' 1e12')),
        ('12e+1', Decimal(' 12e1')),
        # upper E, plus
        ('1.0E+12', Decimal(' 1e12')),
        ('1E+12', Decimal(' 1e12')),
        ('12E+1', Decimal(' 12e1')),
        # lower E, unsigned
        ('1.0e12', Decimal(' 1e12')),
        ('1e12', Decimal(' 1e12')),
        ('12e1', Decimal(' 12e1')),
        # upper E, unsigned
        ('1.0E12', Decimal(' 1e12')),
        ('1E12', Decimal(' 1e12')),
        ('12E1', Decimal(' 12e1')),
    ],
)
def test_validate_scientific_notation_from_json(input_value, expected):
    v = SchemaValidator({'type': 'decimal'})
    assert v.validate_json(input_value) == expected
