import math
import re
import sys
from decimal import Decimal
from typing import Any

import pytest
from dirty_equals import FunctionCheck, IsFloatNan, IsStr

from pydantic_core import SchemaValidator, ValidationError, core_schema
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson, plain_repr

i64_max = (2**63) - 1
f64_max = sys.float_info.max


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, 0),
        (1, 1),
        (42, 42),
        (i64_max + 1, i64_max + 1),
        (f64_max, f64_max),
        ('42', 42),
        ('  42.1  ', 42.1),
        ('42.123', 42.123),
        (42.0, 42),
        (42.5, 42.5),
        (1e10, 1e10),
        (True, 1),
        (False, 0),
        ('wrong', Err('Input should be a valid number, unable to parse string as a number [type=float_parsing')),
        ([1, 2], Err('Input should be a valid number [type=float_type, input_value=[1, 2], input_type=list]')),
    ],
)
def test_float(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'float'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, float)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, 0),
        (1, 1),
        (42, 42),
        (42.0, 42.0),
        (42.5, 42.5),
        ('42', Err("Input should be a valid number [type=float_type, input_value='42', input_type=str]")),
        (True, Err('Input should be a valid number [type=float_type, input_value=True, input_type=bool]')),
    ],
    ids=repr,
)
def test_float_strict(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'float', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, float)


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 0, 0),
        ({}, '123.456', 123.456),
        ({'ge': 0}, 0, 0),
        (
            {'ge': 0},
            -0.1,
            Err(
                'Input should be greater than or equal to 0 '
                '[type=greater_than_equal, input_value=-0.1, input_type=float]'
            ),
        ),
        ({'gt': 0}, 0.1, 0.1),
        ({'gt': 0}, 0, Err('Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]')),
        ({'le': 0}, 0, 0),
        ({'le': 0}, -1, -1),
        ({'le': 0}, 0.1, Err('Input should be less than or equal to 0')),
        ({'lt': 0}, 0, Err('Input should be less than 0')),
        ({'lt': 0.123456}, 1, Err('Input should be less than 0.123456')),
        ({'lt': 0, 'allow_inf_nan': True}, float('nan'), Err('Input should be less than 0')),
        ({'gt': 0, 'allow_inf_nan': True}, float('inf'), float('inf')),
    ],
)
def test_float_kwargs(py_and_json: PyAndJson, kwargs: dict[str, Any], input_value, expected):
    v = py_and_json({'type': 'float', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, float)


@pytest.mark.parametrize(
    'multiple_of,input_value,error',
    [
        # Test cases for multiples of 0.5
        *[(0.5, round(i * 0.5, 1), None) for i in range(-4, 5)],
        (0.5, 0.49, Err('Input should be a multiple of 0.5')),
        (0.5, 0.6, Err('Input should be a multiple of 0.5')),
        (0.5, -0.75, Err('Input should be a multiple of 0.5')),
        (0.5, 0.501, Err('Input should be a multiple of 0.5')),
        (0.5, 1_000_000.5, None),
        (0.5, 1_000_000.49, Err('Input should be a multiple of 0.5')),
        (0.5, int(5e10), None),
        # Test cases for multiples of 0.1
        *[(0.1, round(i * 0.1, 1), None) for i in range(-10, 11)],
        (0.1, 0, None),
        (0.1, 0.5001, Err('Input should be a multiple of 0.1')),
        (0.1, 0.05, Err('Input should be a multiple of 0.1')),
        (0.1, -0.15, Err('Input should be a multiple of 0.1')),
        (0.1, 1_000_000.1, None),
        (0.1, 1_000_000.05, Err('Input should be a multiple of 0.1')),
        (0.1, 1, None),
        (0.1, int(5e10), None),
        # Test cases for multiples of 2.0
        *[(2.0, i * 2.0, None) for i in range(-5, 6)],
        (2.0, -2.1, Err('Input should be a multiple of 2')),
        (2.0, -3.0, Err('Input should be a multiple of 2')),
        (2.0, 1_000_002.0, None),
        (2.0, 1_000_001.0, Err('Input should be a multiple of 2')),
        (2.0, int(5e10), None),
        # Test cases for multiples of 0.01
        *[(0.01, round(i * 0.01, 2), None) for i in range(-10, 11)],
        (0.01, 0.005, Err('Input should be a multiple of 0.01')),
        (0.01, -0.015, Err('Input should be a multiple of 0.01')),
        (0.01, 1_000_000.01, None),
        (0.01, 1_000_000.005, Err('Input should be a multiple of 0.01')),
        (0.01, int(5e10), None),
        # Test cases for values very close to zero
        (0.1, 0.00001, Err('Input should be a multiple of 0.1')),
        (0.1, -0.00001, Err('Input should be a multiple of 0.1')),
        (0.01, 0.00001, Err('Input should be a multiple of 0.01')),
        (0.01, -0.00001, Err('Input should be a multiple of 0.01')),
    ],
    ids=repr,
)
def test_float_multiple_of(py_and_json: PyAndJson, multiple_of, input_value, error):
    v = py_and_json({'type': 'float', 'multiple_of': multiple_of})
    if error:
        with pytest.raises(ValidationError, match=re.escape(error.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == input_value
        assert isinstance(output, float)


def test_union_float(py_and_json: PyAndJson):
    v = py_and_json(
        {'type': 'union', 'choices': [{'type': 'float', 'strict': True}, {'type': 'float', 'multiple_of': 7}]}
    )
    assert v.validate_test('14') == 14
    assert v.validate_test(5) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('5')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'float_type', 'loc': ('float',), 'msg': 'Input should be a valid number', 'input': '5'},
        {
            'type': 'multiple_of',
            'loc': ('constrained-float',),
            'msg': 'Input should be a multiple of 7',
            'input': '5',
            'ctx': {'multiple_of': 7.0},
        },
    ]


def test_union_float_simple(py_and_json: PyAndJson):
    v = py_and_json({'type': 'union', 'choices': [{'type': 'float'}, {'type': 'list'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'float_parsing',
            'loc': ('float',),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'xxx',
        },
        {
            'type': 'list_type',
            'loc': ('list[any]',),
            'msg': IsStr(regex='Input should be a valid (list|array)'),
            'input': 'xxx',
        },
    ]


def test_float_repr():
    v = SchemaValidator(cs.float_schema())
    assert (
        plain_repr(v)
        == 'SchemaValidator(title="float",validator=Float(FloatValidator{strict:false,allow_inf_nan:true}),definitions=[],cache_strings=True)'
    )
    v = SchemaValidator(cs.float_schema(strict=True))
    assert (
        plain_repr(v)
        == 'SchemaValidator(title="float",validator=Float(FloatValidator{strict:true,allow_inf_nan:true}),definitions=[],cache_strings=True)'
    )
    v = SchemaValidator(cs.float_schema(multiple_of=7))
    assert plain_repr(v).startswith('SchemaValidator(title="constrained-float",validator=ConstrainedFloat(')


@pytest.mark.parametrize('input_value,expected', [(Decimal('1.23'), 1.23), (Decimal('1'), 1.0)])
def test_float_not_json(input_value, expected):
    v = SchemaValidator(cs.float_schema())
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, float)


def test_float_nan(py_and_json: PyAndJson):
    v = py_and_json({'type': 'float'})
    assert v.validate_test('1' * 800) == float('inf')
    assert v.validate_test('-' + '1' * 800) == float('-inf')
    r = v.validate_test('nan')
    assert math.isnan(r)


def test_float_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'float'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 1, '2': 2}) == {1: 1, 2: 2}
    assert v.validate_test({'1.5': 1, '2.4': 2}) == {1.5: 1, 2.4: 2}
    with pytest.raises(ValidationError, match='Input should be a valid number'):
        v.validate_python({'1.5': 1, '2.5': 2}, strict=True)
    assert v.validate_json('{"1.5": 1, "2.5": 2}', strict=True) == {1.5: 1, 2.5: 2}


@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        ('NaN', True, FunctionCheck(math.isnan)),
        ('NaN', False, Err("Input should be a finite number [type=finite_number, input_value='NaN', input_type=str]")),
        ('+inf', True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
        ('inf', True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
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
        ('0.7', True, 0.7),
        ('0.7', False, 0.7),
        (
            'pika',
            True,
            Err(
                'Input should be a valid number, unable to parse string as a number '
                "[type=float_parsing, input_value='pika', input_type=str]"
            ),
        ),
        (
            'pika',
            False,
            Err(
                'Input should be a valid number, unable to parse string as a number '
                "[type=float_parsing, input_value='pika', input_type=str]"
            ),
        ),
    ],
)
def test_non_finite_json_values(py_and_json: PyAndJson, input_value, allow_inf_nan, expected):
    v = py_and_json({'type': 'float', 'allow_inf_nan': allow_inf_nan})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('strict', (True, False))
@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        (float('nan'), True, FunctionCheck(math.isnan)),
        (
            float('nan'),
            False,
            Err('Input should be a finite number [type=finite_number, input_value=nan, input_type=float]'),
        ),
    ],
)
def test_non_finite_float_values(strict, input_value, allow_inf_nan, expected):
    v = SchemaValidator(cs.float_schema(allow_inf_nan=allow_inf_nan, strict=strict))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,allow_inf_nan,expected',
    [
        (float('+inf'), True, FunctionCheck(lambda x: math.isinf(x) and x > 0)),
        (
            float('+inf'),
            False,
            Err('Input should be a finite number [type=finite_number, input_value=inf, input_type=float]'),
        ),
        (
            float('-inf'),
            True,
            Err('Input should be greater than 0 [type=greater_than, input_value=-inf, input_type=float]'),
        ),
        (
            float('-inf'),
            False,
            Err('Input should be a finite number [type=finite_number, input_value=-inf, input_type=float]'),
        ),
    ],
)
def test_non_finite_constrained_float_values(input_value, allow_inf_nan, expected):
    v = SchemaValidator(cs.float_schema(allow_inf_nan=allow_inf_nan, gt=0))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        # lower e, minus
        ('1.0e-12', 1e-12),
        ('1e-12', 1e-12),
        ('12e-1', 12e-1),
        # upper E, minus
        ('1.0E-12', 1e-12),
        ('1E-12', 1e-12),
        ('12E-1', 12e-1),
        # lower E, plus
        ('1.0e+12', 1e12),
        ('1e+12', 1e12),
        ('12e+1', 12e1),
        # upper E, plus
        ('1.0E+12', 1e12),
        ('1E+12', 1e12),
        ('12E+1', 12e1),
        # lower E, unsigned
        ('1.0e12', 1e12),
        ('1e12', 1e12),
        ('12e1', 12e1),
        # upper E, unsigned
        ('1.0E12', 1e12),
        ('1E12', 1e12),
        ('12E1', 12e1),
    ],
)
def test_validate_scientific_notation_from_json(input_value, expected):
    v = SchemaValidator(cs.float_schema())
    assert v.validate_json(input_value) == expected


def test_string_with_underscores() -> None:
    v = SchemaValidator(cs.float_schema())
    assert v.validate_python('1_000_000.0') == 1_000_000.0
    assert v.validate_json('"1_000_000.0"') == 1_000_000.0

    for edge_case in ('_1', '_1.0', '1__0', '1.1__1', '1_0.0_', '1._', '1_0__0.0'):
        with pytest.raises(ValidationError):
            v.validate_python(edge_case)
        with pytest.raises(ValidationError):
            v.validate_json(f'"{edge_case}"')


def test_allow_inf_nan_true_json() -> None:
    v = SchemaValidator(core_schema.float_schema())

    assert v.validate_json('123') == 123
    assert v.validate_json('NaN') == IsFloatNan()
    assert v.validate_json('Infinity') == float('inf')
    assert v.validate_json('-Infinity') == float('-inf')

    assert v.validate_json('"NaN"') == IsFloatNan()
    assert v.validate_json('"Infinity"') == float('inf')
    assert v.validate_json('"-Infinity"') == float('-inf')


def test_allow_inf_nan_false_json() -> None:
    v = SchemaValidator(core_schema.float_schema(), config=core_schema.CoreConfig(allow_inf_nan=False))

    assert v.validate_json('123') == 123
    with pytest.raises(ValidationError) as exc_info1:
        v.validate_json('NaN')
    # insert_assert(exc_info.value.errors())
    assert exc_info1.value.errors(include_url=False) == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': IsFloatNan()}
    ]
    with pytest.raises(ValidationError) as exc_info2:
        v.validate_json('Infinity')
    assert exc_info2.value.errors(include_url=False) == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': float('inf')}
    ]
    with pytest.raises(ValidationError) as exc_info3:
        v.validate_json('-Infinity')
    assert exc_info3.value.errors(include_url=False) == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': float('-inf')}
    ]
