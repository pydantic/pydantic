import re

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


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
                "unable to interpret input [kind=bool_parsing, input_value='cheese', input_type=str]"
            ),
        ),
        (2, Err('Value must be a valid boolean, unable to interpret input [kind=bool_parsing, input_value=2')),
        ([], Err('Value must be a valid boolean [kind=bool_type, input_value=[], input_type=list]')),
    ],
)
def test_bool(py_or_json, input_value, expected):
    v = py_or_json({'type': 'bool'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
        assert v.isinstance_test(input_value) is False
    else:
        assert v.validate_test(input_value) == expected
        assert v.isinstance_test(input_value) is True


def test_bool_strict(py_or_json):
    v = py_or_json({'type': 'bool', 'strict': True})
    assert v.validate_test(True) is True
    error_message = "Value must be a valid boolean [kind=bool_type, input_value='true', input_type=str]"
    with pytest.raises(ValidationError, match=re.escape(error_message)):
        v.validate_test('true')


def test_bool_error():
    v = SchemaValidator({'type': 'bool'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    assert str(exc_info.value) == (
        '1 validation error for bool\n'
        '  Value must be a valid boolean, '
        "unable to interpret input [kind=bool_parsing, input_value='wrong', input_type=str]"
    )
    assert exc_info.value.errors() == [
        {
            'kind': 'bool_parsing',
            'loc': [],
            'message': 'Value must be a valid boolean, unable to interpret input',
            'input_value': 'wrong',
        }
    ]


def test_bool_repr():
    v = SchemaValidator({'type': 'bool'})
    assert repr(v) == 'SchemaValidator(name="bool", validator=Bool(\n    BoolValidator,\n))'
    v = SchemaValidator({'type': 'bool', 'strict': True})
    assert repr(v) == 'SchemaValidator(name="strict-bool", validator=StrictBool(\n    StrictBoolValidator,\n))'
