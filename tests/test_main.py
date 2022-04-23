import re
from dataclasses import dataclass

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


@dataclass
class Err:
    message: str


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (False, False),
        (True, True),
        (0, False),
        (1, True),
        ('yes', True),
        ('no', False),
        ('true', True),
        ('false', False),
        (
            'cheese',
            Err(
                'Value must be a valid boolean, '
                'unable to interpret input [kind=bool_parsing, input_value=cheese, input_type=str]'
            ),
        ),
    ],
)
def test_bool(input_value, expected):
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_bool_strict():
    v = SchemaValidator({'type': 'bool', 'strict': True, 'title': 'TestModel'})
    assert v.validate_python(True) is True
    error_message = 'Value must be a valid boolean [kind=bool_type, input_value=true, input_type=str]'
    with pytest.raises(ValidationError, match=re.escape(error_message)):
        v.validate_python('true')


def test_bool_error():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    assert str(exc_info.value) == (
        '1 validation error for TestModel\n'
        '  Value must be a valid boolean, '
        'unable to interpret input [kind=bool_parsing, input_value=wrong, input_type=str]'
    )
    assert exc_info.value.errors() == [
        {
            'kind': 'bool_parsing',
            'loc': [],
            'message': 'Value must be a valid boolean, unable to interpret input',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (False, False),
        (True, True),
        (0, 0),
        ('0', 0),
        (1, 1),
        (42, 42),
        ('42', 42),
        (42.0, 42),
        (int(1e10), int(1e10)),
        (True, 1),
        (False, 0),
        (12.5, Err('Value must be a valid integer, got a number with a fractional part [kind=int_from_float')),
        ('wrong', Err('Value must be a valid integer, unable to parse string as an integer [kind=int_parsing')),
        ((1, 2), Err('Value must be a valid integer [kind=int_type, input_value=(1, 2), input_type=tuple]')),
    ],
)
def test_int(input_value, expected):
    v = SchemaValidator({'type': 'int', 'title': 'TestModel'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_bool_repr():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=BoolValidator)'
    v = SchemaValidator({'type': 'bool', 'strict': True, 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=StrictBoolValidator)'


def test_str_constrained():
    v = SchemaValidator({'type': 'str', 'max_length': 5, 'title': 'TestModel'})
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
def test_str(input_value, expected):
    v = SchemaValidator({'type': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
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
def test_constrained_str(kwargs, input_value, expected):
    v = SchemaValidator({'type': 'str', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


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
