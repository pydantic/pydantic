import re

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


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
        ('wrong', Err('Value must be a valid number, unable to parse string as an number [kind=float_parsing')),
        ([1, 2], Err('Value must be a valid number [kind=float_type, input_value=[1, 2], input_type=list]')),
    ],
)
def test_float(py_or_json, input_value, expected):
    v = py_or_json({'type': 'float'})
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
        pytest.param(
            '42', Err("Value must be a valid number [kind=float_type, input_value='42', input_type=str]"), id='string'
        ),
        pytest.param(
            True, Err('Value must be a valid number [kind=float_type, input_value=True, input_type=bool]'), id='bool'
        ),
    ],
)
def test_float_strict(py_or_json, input_value, expected):
    v = py_or_json({'type': 'float', 'strict': True})
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
                'Value must be greater than or equal to 0 '
                '[kind=float_greater_than_equal, context={ge: 0}, input_value=-0.1, input_type=float]'
            ),
        ),
        ({'gt': 0}, 0.1, 0.1),
        (
            {'gt': 0},
            0,
            Err(
                'Value must be greater than 0 [kind=float_greater_than, context={gt: 0}, input_value=0, input_type=int]'
            ),
        ),
        ({'le': 0}, 0, 0),
        ({'le': 0}, -1, -1),
        ({'le': 0}, 0.1, Err('Value must be less than or equal to 0')),
        ({'lt': 0}, 0, Err('Value must be less than 0')),
        ({'lt': 0.123456}, 1, Err('Value must be less than 0.123456')),
        ({'multiple_of': 0.5}, 0.5, 0.5),
        ({'multiple_of': 0.5}, 1, 1),
        ({'multiple_of': 0.5}, 0.6, Err('Value must be a multiple of 0.5')),
    ],
)
def test_float_kwargs(py_or_json, kwargs, input_value, expected):
    v = py_or_json({'type': 'float', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, float)


def test_union_float(py_or_json):
    v = py_or_json(
        {'type': 'union', 'choices': [{'type': 'float', 'strict': True}, {'type': 'float', 'multiple_of': 7}]}
    )
    assert v.validate_test('14') == 14
    assert v.validate_test(5) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('5')
    assert exc_info.value.errors() == [
        {'kind': 'float_type', 'loc': ['strict-float'], 'message': 'Value must be a valid number', 'input_value': '5'},
        {
            'kind': 'float_multiple',
            'loc': ['constrained-float'],
            'message': 'Value must be a multiple of 7',
            'input_value': '5',
            'context': {'multiple_of': 7.0},
        },
    ]


def test_union_float_simple(py_or_json):
    v = py_or_json({'type': 'union', 'choices': [{'type': 'float'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors() == [
        {
            'kind': 'float_parsing',
            'loc': ['float'],
            'message': 'Value must be a valid number, unable to parse string as an number',
            'input_value': 'xxx',
        }
    ]


def test_float_repr():
    v = SchemaValidator({'type': 'float'})
    assert repr(v) == 'SchemaValidator(name="float", validator=FloatValidator)'
    v = SchemaValidator({'type': 'float', 'strict': True})
    assert repr(v) == 'SchemaValidator(name="strict-float", validator=StrictFloatValidator)'
    v = SchemaValidator({'type': 'float', 'multiple_of': 7})
    assert repr(v).startswith('SchemaValidator(name="constrained-float", validator=ConstrainedFloatValidator {\n')
