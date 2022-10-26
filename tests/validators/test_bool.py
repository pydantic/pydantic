import re

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (False, False),
        (True, True),
        (0, False),
        (0.0, False),
        (1, True),
        (1.0, True),
        ('yes', True),
        ('no', False),
        ('true', True),
        ('false', False),
        (
            'cheese',
            Err(
                'Input should be a valid boolean, '
                "unable to interpret input [type=bool_parsing, input_value='cheese', input_type=str]"
            ),
        ),
        (2, Err('Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value=2')),
        ([], Err('Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]')),
        (1.1, Err('Input should be a valid boolean [type=bool_type, input_value=1.1, input_type=float]')),
        (2, Err('unable to interpret input [type=bool_parsing, input_value=2, input_type=int]')),
        (2.0, Err('unable to interpret input [type=bool_parsing, input_value=2.0, input_type=float]')),
    ],
)
def test_bool(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'bool'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
        assert v.isinstance_test(input_value) is False
    else:
        assert v.validate_test(input_value) == expected
        assert v.isinstance_test(input_value) is True


def test_bool_strict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'bool', 'strict': True})
    assert v.validate_test(True) is True
    error_message = "Input should be a valid boolean [type=bool_type, input_value='true', input_type=str]"
    with pytest.raises(ValidationError, match=re.escape(error_message)):
        v.validate_test('true')


def test_bool_error():
    v = SchemaValidator({'type': 'bool'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    assert str(exc_info.value) == (
        '1 validation error for bool\n'
        '  Input should be a valid boolean, '
        "unable to interpret input [type=bool_parsing, input_value='wrong', input_type=str]"
    )
    assert exc_info.value.errors() == [
        {
            'type': 'bool_parsing',
            'loc': (),
            'msg': 'Input should be a valid boolean, unable to interpret input',
            'input': 'wrong',
        }
    ]


def test_bool_repr():
    v = SchemaValidator({'type': 'bool'})
    assert plain_repr(v) == 'SchemaValidator(name="bool",validator=Bool(BoolValidator{strict:false}),slots=[])'
    v = SchemaValidator({'type': 'bool', 'strict': True})
    assert plain_repr(v) == 'SchemaValidator(name="bool",validator=Bool(BoolValidator{strict:true}),slots=[])'


def test_bool_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'bool'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({True: 1, False: 2}) == {True: 1, False: 2}
    assert v.validate_test({'true': 1, 'off': 2}) == {True: 1, False: 2}
    assert v.validate_test({'true': 1, 'off': 2}, strict=False) == {True: 1, False: 2}
    with pytest.raises(ValidationError, match='Input should be a valid boolean'):
        v.validate_test({'true': 1, 'off': 2}, strict=True)
