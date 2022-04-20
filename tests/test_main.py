import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


@pytest.mark.parametrize(
    'input_value,output_value',
    [
        (False, False),
        (True, True),
        (0, False),
        (1, True),
        ('yes', True),
        ('no', False),
        ('true', True),
        ('false', False),
    ],
)
def test_bool(input_value, output_value):
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert v.validate_python(input_value) == output_value


def test_bool_error():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=BoolValidator)'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    assert str(exc_info.value) == (
        '1 validation error for TestModel\n'
        '  Value must be a valid boolean, '
        'unable to interpret input [kind=bool_parsing, input_value=wrong, input_type=str]'
    )


def test_repr():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=BoolValidator)'


def test_str_constrained():
    v = SchemaValidator({'type': 'str-constrained', 'max_length': 5, 'title': 'TestModel'})
    assert v.validate_python('test') == 'test'

    with pytest.raises(ValidationError, match='String must have at most 5 characters'):
        v.validate_python('test long')


@pytest.mark.parametrize(
    'input_value,output_value,error_msg',
    [('foobar', 'foobar', None), (123, '123', None), (False, None, 'Value must be a valid string [kind=str_type')],
)
def test_str(input_value, output_value, error_msg):
    v = SchemaValidator({'type': 'str'})
    if error_msg:
        assert output_value is None, 'output_value should be None if error_msg is set'

        with pytest.raises(ValidationError, match=re.escape(error_msg)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == output_value


@pytest.mark.parametrize(
    'kwargs,input_value,output_value,error_msg',
    [
        ({'to_upper': True}, 'fooBar', 'FOOBAR', None),
        ({'to_lower': True}, 'fooBar', 'foobar', None),
        ({'strip_whitespace': True}, ' foobar  ', 'foobar', None),
        ({'strip_whitespace': True, 'to_upper': True}, ' fooBar', 'FOOBAR', None),
        ({'min_length': 5}, '12345', '12345', None),
        ({'min_length': 5}, '1234', None, 'String must have at least 5 characters [kind=str_too_short'),
        ({'max_length': 5}, '12345', '12345', None),
        ({'max_length': 5}, '123456', None, 'String must have at most 5 characters [kind=str_too_long'),
        ({'pattern': r'^\d+$'}, '12345', '12345', None),
        ({'pattern': r'\d+$'}, 'foobar 123', 'foobar 123', None),
        ({'pattern': r'^\d+$'}, '12345a', None, "String must match pattern '^\\d+$' [kind=str_pattern_mismatch"),
        # strip comes after length check
        ({'max_length': 5, 'strip_whitespace': True}, '1234  ', None, 'String must have at most 5 characters'),
        # to_upper and strip comes after pattern check
        ({'to_upper': True, 'pattern': 'abc'}, 'abc', 'ABC', None),
        ({'strip_whitespace': True, 'pattern': r'\d+$'}, 'foobar 123 ', None, "String must match pattern '\\d+$'"),
    ],
)
def test_constrained_str(kwargs, input_value, output_value, error_msg):
    v = SchemaValidator({'type': 'str-constrained', **kwargs})
    if error_msg:
        assert output_value is None, 'output_value should be None if error_msg is set'

        with pytest.raises(ValidationError, match=re.escape(error_msg)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == output_value


def test_invalid_regex():
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'str-constrained', 'pattern': 123})
    assert exc_info.value.args[0] == (
        'Error building "str-constrained" validator:\n' "  TypeError: 'int' object cannot be converted to 'PyString'"
    )
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'str-constrained', 'pattern': '(abc'})
    assert exc_info.value.args[0] == (
        'Error building "str-constrained" validator:\n'
        '  SchemaError: regex parse error:\n'
        '    (abc\n'
        '    ^\n'
        'error: unclosed group'
    )
