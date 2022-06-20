import re
from decimal import Decimal

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (False, 0),
        (True, 1),
        (0, 0),
        ('0', 0),
        (1, 1),
        (42, 42),
        ('42', 42),
        (42.0, 42),
        (int(1e10), int(1e10)),
        pytest.param(
            12.5,
            Err('Value must be a valid integer, got a number with a fractional part [kind=int_from_float'),
            id='float-remainder',
        ),
        pytest.param(
            'wrong',
            Err('Value must be a valid integer, unable to parse string as an integer [kind=int_parsing'),
            id='string',
        ),
        pytest.param(None, Err('Value must be a valid integer [kind=int_type'), id='list'),
        pytest.param([1, 2], Err('Value must be a valid integer [kind=int_type'), id='list'),
    ],
)
def test_int_py_or_json(py_or_json, input_value, expected):
    v = py_or_json({'type': 'int'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, int)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Decimal('1'), 1),
        (Decimal('1.0'), 1),
        pytest.param(
            Decimal('1.001'),
            Err(
                'Value must be a valid integer, got a number with a fractional part '
                "[kind=int_from_float, input_value=Decimal('1.001'), input_type=Decimal]"
            ),
            id='decimal-remainder',
        ),
        pytest.param(
            (1, 2),
            Err('Value must be a valid integer [kind=int_type, input_value=(1, 2), input_type=tuple]'),
            id='tuple',
        ),
    ],
)
def test_int(input_value, expected):
    v = SchemaValidator({'type': 'int'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, int)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, 0),
        (1, 1),
        (42, 42),
        pytest.param(
            42.0,
            Err('Value must be a valid integer [kind=int_type, input_value=42.0, input_type=float]'),
            id='float-exact',
        ),
        pytest.param(
            42.5,
            Err('Value must be a valid integer [kind=int_type, input_value=42.5, input_type=float]'),
            id='float-remainder',
        ),
        pytest.param(
            '42', Err("Value must be a valid integer [kind=int_type, input_value='42', input_type=str]"), id='string'
        ),
        pytest.param(
            True, Err('Value must be a valid integer [kind=int_type, input_value=True, input_type=bool]'), id='bool'
        ),
    ],
)
def test_int_strict(py_or_json, input_value, expected):
    v = py_or_json({'type': 'int', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        pytest.param({}, 0, 0),
        pytest.param({}, '123.000', 123),
        pytest.param({'ge': 0}, 0, 0),
        pytest.param(
            {'ge': 0},
            -1,
            Err(
                'Value must be greater than or equal to 0 '
                '[kind=greater_than_equal, context={ge: 0}, input_value=-1, input_type=int]'
            ),
            id='ge-0',
        ),
        pytest.param({'gt': 0}, 1, 1),
        pytest.param(
            {'gt': 0},
            0,
            Err('Value must be greater than 0 [kind=greater_than, context={gt: 0}, input_value=0, input_type=int]'),
            id='gt-0',
        ),
        pytest.param({'le': 0}, 0, 0),
        pytest.param({'le': 0}, -1, -1),
        pytest.param({'le': 0}, 1, Err('Value must be less than or equal to 0'), id='le-0'),
        pytest.param({'lt': 0}, 0, Err('Value must be less than 0'), id='lt-0'),
        pytest.param({'lt': 0}, 1, Err('Value must be less than 0'), id='lt-0'),
        pytest.param({'multiple_of': 5}, 15, 15),
        pytest.param({'multiple_of': 5}, 6, Err('Value must be a multiple of 5'), id='multiple_of-5'),
    ],
)
def test_int_kwargs(py_or_json, kwargs, input_value, expected):
    v = py_or_json({'type': 'int', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, int)


def test_union_int(py_or_json):
    v = py_or_json({'type': 'union', 'choices': [{'type': 'int', 'strict': True}, {'type': 'int', 'multiple_of': 7}]})
    assert v.validate_test('14') == 14
    assert v.validate_test(5) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('5')

    assert exc_info.value.errors() == [
        {'kind': 'int_type', 'loc': ['strict-int'], 'message': 'Value must be a valid integer', 'input_value': '5'},
        {
            'kind': 'int_multiple',
            'loc': ['constrained-int'],
            'message': 'Value must be a multiple of 7',
            'input_value': '5',
            'context': {'multiple_of': 7},
        },
    ]


def test_union_int_simple(py_or_json):
    v = py_or_json({'type': 'union', 'choices': [{'type': 'int'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['int'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'xxx',
        }
    ]


def test_int_repr():
    v = SchemaValidator({'type': 'int'})
    assert repr(v) == 'SchemaValidator(name="int", validator=Int(\n    IntValidator,\n))'
    v = SchemaValidator({'type': 'int', 'strict': True})
    assert repr(v) == 'SchemaValidator(name="strict-int", validator=StrictInt(\n    StrictIntValidator,\n))'
    v = SchemaValidator({'type': 'int', 'multiple_of': 7})
    assert repr(v).startswith('SchemaValidator(name="constrained-int", validator=ConstrainedInt(\n')


def test_long_int(py_or_json):
    v = py_or_json({'type': 'int'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('1' * 400)

    assert exc_info.value.errors() == [
        {
            'kind': 'int_nan',
            'loc': [],
            'message': 'Value must be a valid integer, got infinity',
            'input_value': '1' * 400,
            'context': {'nan_value': 'infinity'},
        }
    ]
    assert repr(exc_info.value) == (
        '1 validation error for int\n'
        '  Value must be a valid integer, got infinity '
        '[kind=int_nan, context={nan_value: infinity}, '
        "input_value='111111111111111111111111...11111111111111111111111', input_type=str]"
    )


def test_int_nan(py_or_json):
    v = py_or_json({'type': 'int'})

    with pytest.raises(ValidationError, match='Value must be a valid integer, got negative infinity'):
        v.validate_test('-' + '1' * 400)

    with pytest.raises(ValidationError, match='Value must be a valid integer, got NaN'):
        v.validate_test('nan')
