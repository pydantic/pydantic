import math
import re
from decimal import Decimal
from typing import Any, Dict

import pytest
from dirty_equals import FunctionCheck

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, 0),
        (1, 1),
        (42, 42),
        ('42', 42),
        ('42.123', 42.123),
        (42.0, 42),
        (42.5, 42.5),
        (1e10, 1e10),
        (True, 1),
        (False, 0),
        ('wrong', Err('Input should be a valid number, unable to parse string as an number [type=float_parsing')),
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
    ],
)
def test_float_kwargs(py_and_json: PyAndJson, kwargs: Dict[str, Any], input_value, expected):
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
    assert exc_info.value.errors() == [
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

    assert exc_info.value.errors() == [
        {
            'type': 'float_parsing',
            'loc': ('float',),
            'msg': 'Input should be a valid number, unable to parse string as an number',
            'input': 'xxx',
        },
        {'type': 'list_type', 'loc': ('list[any]',), 'msg': 'Input should be a valid list/array', 'input': 'xxx'},
    ]


def test_float_repr():
    v = SchemaValidator({'type': 'float'})
    assert (
        plain_repr(v)
        == 'SchemaValidator(name="float",validator=Float(FloatValidator{strict:false,allow_inf_nan:true}),slots=[])'
    )
    v = SchemaValidator({'type': 'float', 'strict': True})
    assert (
        plain_repr(v)
        == 'SchemaValidator(name="float",validator=Float(FloatValidator{strict:true,allow_inf_nan:true}),slots=[])'
    )
    v = SchemaValidator({'type': 'float', 'multiple_of': 7})
    assert plain_repr(v).startswith('SchemaValidator(name="constrained-float",validator=ConstrainedFloat(')


@pytest.mark.parametrize('input_value,expected', [(Decimal('1.23'), 1.23), (Decimal('1'), 1.0)])
def test_float_not_json(input_value, expected):
    v = SchemaValidator({'type': 'float'})
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
        v.validate_test({'1.5': 1, '2.5': 2}, strict=True)


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
        ('0.7', True, 0.7),
        ('0.7', False, 0.7),
        (
            'pika',
            True,
            Err(
                'Input should be a valid number, unable to parse string as an number '
                "[type=float_parsing, input_value='pika', input_type=str]"
            ),
        ),
        (
            'pika',
            False,
            Err(
                'Input should be a valid number, unable to parse string as an number '
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
    v = SchemaValidator({'type': 'float', 'allow_inf_nan': allow_inf_nan, 'strict': strict})
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
    v = SchemaValidator({'type': 'float', 'allow_inf_nan': allow_inf_nan, 'gt': 0})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected
