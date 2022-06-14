import re
from decimal import Decimal

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err


def test_str_constrained():
    v = SchemaValidator({'type': 'str', 'max_length': 5})
    assert v.validate_python('test') == 'test'

    with pytest.raises(ValidationError, match='String must have at most 5 characters'):
        v.validate_python('test long')


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('foobar', 'foobar'),
        (123, '123'),
        (123.456, '123.456'),
        (False, Err('Value must be a valid string [kind=str_type')),
        (True, Err('Value must be a valid string [kind=str_type')),
        ([], Err('Value must be a valid string [kind=str_type, input_value=[], input_type=list]')),
    ],
)
def test_str(py_or_json, input_value, expected):
    v = py_or_json({'type': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('foobar', 'foobar'),
        (b'foobar', 'foobar'),
        (b'\x81', Err('Value must be a valid string, unable to parse raw data as a unicode string [kind=str_unicode')),
        # null bytes are very annoying, but we can't really block them here
        (b'\x00', '\x00'),
        (123, '123'),
        (Decimal('123'), '123'),
    ],
)
def test_str_not_json(input_value, expected):
    v = SchemaValidator({'type': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 123, '123'),
        ({'strict': True}, 'Foobar', 'Foobar'),
        ({'strict': True}, 123, Err('Value must be a valid string [kind=str_type, input_value=123, input_type=int]')),
        ({'to_upper': True}, 'fooBar', 'FOOBAR'),
        ({'to_lower': True}, 'fooBar', 'foobar'),
        ({'strip_whitespace': True}, ' foobar  ', 'foobar'),
        ({'strip_whitespace': True, 'to_upper': True}, ' fooBar', 'FOOBAR'),
        ({'min_length': 5}, '12345', '12345'),
        ({'min_length': 5}, '1234', Err('String must have at least 5 characters [kind=str_too_short')),
        ({'max_length': 5}, '12345', '12345'),
        ({'max_length': 5}, '123456', Err('String must have at most 5 characters [kind=str_too_long')),
        ({'pattern': r'^\d+$'}, '12345', '12345'),
        ({'pattern': r'\d+$'}, 'foobar 123', 'foobar 123'),
        ({'pattern': r'^\d+$'}, '12345a', Err("String must match pattern '^\\d+$' [kind=str_pattern_mismatch")),
        # strip comes after length check
        ({'max_length': 5, 'strip_whitespace': True}, '1234  ', Err('String must have at most 5 characters')),
        # to_upper and strip comes after pattern check
        ({'to_upper': True, 'pattern': 'abc'}, 'abc', 'ABC'),
        ({'strip_whitespace': True, 'pattern': r'\d+$'}, 'foobar 123 ', Err("String must match pattern '\\d+$'")),
    ],
)
def test_constrained_str(py_or_json, kwargs, input_value, expected):
    v = py_or_json({'type': 'str', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_invalid_regex():
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'str', 'pattern': 123})
    assert exc_info.value.args[0] == (
        'Error building "str" validator:\n  TypeError: \'int\' object cannot be converted to \'PyString\''
    )
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'str', 'pattern': '(abc'})
    assert exc_info.value.args[0] == (
        'Error building "str" validator:\n'
        '  SchemaError: regex parse error:\n'
        '    (abc\n'
        '    ^\n'
        'error: unclosed group'
    )
