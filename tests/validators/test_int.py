import re
from decimal import Decimal
from typing import Any, Dict

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr

i64_max = 9_223_372_036_854_775_807


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
        ('42.0', 42),
        ('123456789.0', 123_456_789),
        ('123456789123456.00001', 123_456_789_123_456),
        (int(1e10), int(1e10)),
        (i64_max, i64_max),
        pytest.param(
            12.5,
            Err('Input should be a valid integer, got a number with a fractional part [type=int_from_float'),
            id='float-remainder',
        ),
        pytest.param(
            'wrong',
            Err('Input should be a valid integer, unable to parse string as an integer [type=int_parsing'),
            id='string',
        ),
        pytest.param(None, Err('Input should be a valid integer [type=int_type'), id='list'),
        pytest.param([1, 2], Err('Input should be a valid integer [type=int_type'), id='list'),
    ],
)
def test_int_py_and_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'int'})
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
        (i64_max, i64_max),
        (i64_max + 1, i64_max),
        (i64_max * 2, i64_max),
        pytest.param(
            Decimal('1.001'),
            Err(
                'Input should be a valid integer, got a number with a fractional part '
                "[type=int_from_float, input_value=Decimal('1.001'), input_type=Decimal]"
            ),
            id='decimal-remainder',
        ),
        pytest.param(
            (1, 2),
            Err('Input should be a valid integer [type=int_type, input_value=(1, 2), input_type=tuple]'),
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
            Err('Input should be a valid integer [type=int_type, input_value=42.0, input_type=float]'),
            id='float-exact',
        ),
        pytest.param(
            42.5,
            Err('Input should be a valid integer [type=int_type, input_value=42.5, input_type=float]'),
            id='float-remainder',
        ),
        pytest.param(
            '42', Err("Input should be a valid integer [type=int_type, input_value='42', input_type=str]"), id='string'
        ),
        pytest.param(
            True, Err('Input should be a valid integer [type=int_type, input_value=True, input_type=bool]'), id='bool'
        ),
    ],
)
def test_int_strict(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'int', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 0, 0),
        ({}, '123.000', 123),
        ({'ge': 0}, 0, 0),
        (
            {'ge': 0},
            -1,
            Err(
                'Input should be greater than or equal to 0 '
                '[type=greater_than_equal, input_value=-1, input_type=int]'
            ),
        ),
        ({'gt': 0}, 1, 1),
        ({'gt': 0}, 0, Err('Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]')),
        ({'le': 0}, 0, 0),
        ({'le': 0}, -1, -1),
        ({'le': 0}, 1, Err('Input should be less than or equal to 0')),
        ({'lt': 0}, 0, Err('Input should be less than 0')),
        ({'lt': 0}, 1, Err('Input should be less than 0')),
        ({'multiple_of': 5}, 15, 15),
        ({'multiple_of': 5}, 6, Err('Input should be a multiple of 5')),
    ],
    ids=repr,
)
def test_int_kwargs(py_and_json: PyAndJson, kwargs: Dict[str, Any], input_value, expected):
    v = py_and_json({'type': 'int', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        if 'ctx' in errors[0]:
            assert errors[0]['ctx'] == kwargs
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, int)


def test_union_int(py_and_json: PyAndJson):
    v = py_and_json({'type': 'union', 'choices': [{'type': 'int', 'strict': True}, {'type': 'int', 'multiple_of': 7}]})
    assert v.validate_test('14') == 14
    assert v.validate_test(5) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('5')

    assert exc_info.value.errors() == [
        {'type': 'int_type', 'loc': ('int',), 'msg': 'Input should be a valid integer', 'input': '5'},
        {
            'type': 'multiple_of',
            'loc': ('constrained-int',),
            'msg': 'Input should be a multiple of 7',
            'input': '5',
            'ctx': {'multiple_of': 7},
        },
    ]


def test_union_int_simple(py_and_json: PyAndJson):
    v = py_and_json({'type': 'union', 'choices': [{'type': 'int'}, {'type': 'list'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('int',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xxx',
        },
        {'type': 'list_type', 'loc': ('list[any]',), 'msg': 'Input should be a valid list/array', 'input': 'xxx'},
    ]


def test_int_repr():
    v = SchemaValidator({'type': 'int'})
    assert plain_repr(v) == 'SchemaValidator(name="int",validator=Int(IntValidator{strict:false}),slots=[])'
    v = SchemaValidator({'type': 'int', 'strict': True})
    assert plain_repr(v) == 'SchemaValidator(name="int",validator=Int(IntValidator{strict:true}),slots=[])'
    v = SchemaValidator({'type': 'int', 'multiple_of': 7})
    assert plain_repr(v).startswith('SchemaValidator(name="constrained-int",validator=ConstrainedInt(')


def test_long_int(py_and_json: PyAndJson):
    v = py_and_json({'type': 'int'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('1' * 400)

    assert exc_info.value.errors() == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': '1' * 400}
    ]
    assert repr(exc_info.value) == (
        '1 validation error for int\n'
        '  Input should be a finite number '
        '[type=finite_number, '
        "input_value='111111111111111111111111...11111111111111111111111', input_type=str]"
    )


def test_finite_number(py_and_json: PyAndJson):
    v = py_and_json({'type': 'int'})

    with pytest.raises(ValidationError, match='Input should be a finite number'):
        v.validate_test('-' + '1' * 400)

    with pytest.raises(ValidationError, match='Input should be a finite number'):
        v.validate_test('nan')


def test_int_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 1, '2': 2}) == {1: 1, 2: 2}
    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_test({'1': 1, '2': 2}, strict=True)
