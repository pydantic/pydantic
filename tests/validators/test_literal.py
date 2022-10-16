import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'kwarg_expected,input_value,expected',
    [
        ([1], 1, 1),
        pytest.param(
            [1],
            2,
            Err('Input should be: 1 [kind=literal_single_error, input_value=2, input_type=int]'),
            id='wrong-single-int',
        ),
        (['foo'], 'foo', 'foo'),
        pytest.param(
            ['foo'],
            'bar',
            Err("Input should be: 'foo' [kind=literal_single_error, input_value='bar', input_type=str]"),
            id='wrong-single-str',
        ),
        ([1, 2], 1, 1),
        ([1, 2], 2, 2),
        pytest.param(
            [1, 2],
            3,
            Err('Input should be one of: 1, 2 [kind=literal_multiple_error, input_value=3, input_type=int]'),
            id='wrong-multiple-int',
        ),
        (['a', 'b'], 'a', 'a'),
        pytest.param(
            ['a', 'b'],
            'c',
            Err("Input should be one of: 'a', 'b' [kind=literal_multiple_error, input_value=\'c\', input_type=str]"),
            id='wrong-multiple-str',
        ),
        ([1, '1'], 1, 1),
        ([1, '1'], '1', '1'),
        pytest.param(
            [1, '1'],
            '2',
            Err("Input should be one of: 1, '1' [kind=literal_multiple_error, input_value='2', input_type=str]"),
            id='wrong-str-int',
        ),
    ],
)
def test_literal_py_and_json(py_and_json: PyAndJson, kwarg_expected, input_value, expected):
    v = py_and_json({'type': 'literal', 'expected': kwarg_expected})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'kwarg_expected,input_value,expected',
    [
        ([1, b'whatever'], b'whatever', b'whatever'),
        ([(1, 2), (3, 4)], (1, 2), (1, 2)),
        ([(1, 2), (3, 4)], (3, 4), (3, 4)),
        pytest.param(
            [1, b'whatever'],
            3,
            Err("Input should be one of: 1, b'whatever' [kind=literal_multiple_error, input_value=3, input_type=int]"),
            id='wrong-general',
        ),
    ],
)
def test_literal_not_json(kwarg_expected, input_value, expected):
    v = SchemaValidator({'type': 'literal', 'expected': kwarg_expected})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_build_error():
    with pytest.raises(SchemaError, match='SchemaError: "expected" should have length > 0'):
        SchemaValidator({'type': 'literal', 'expected': []})


def test_literal_none():
    v = SchemaValidator(core_schema.literal_schema(None))
    assert v.isinstance_python(None) is True
    assert v.isinstance_python(0) is False
    assert v.isinstance_json('null') is True
    assert v.isinstance_json('""') is False
    assert plain_repr(v) == 'SchemaValidator(name="none",validator=None(NoneValidator),slots=[])'
