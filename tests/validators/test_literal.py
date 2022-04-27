import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err


@pytest.mark.parametrize(
    'kwarg_expected,input_value,expected',
    [
        ([1], 1, 1),
        pytest.param(
            [1],
            2,
            Err('Value must be 1 [kind=literal_error, context={expected: 1}, input_value=2, input_type=int]'),
            id='wrong-single-int',
        ),
        (['foo'], 'foo', 'foo'),
        pytest.param(
            ['foo'],
            'bar',
            Err(
                "Value must be 'foo' "
                "[kind=literal_error, context={expected: 'foo'}, input_value='bar', input_type=str]"
            ),
            id='wrong-single-str',
        ),
        ([1, 2], 1, 1),
        ([1, 2], 2, 2),
        pytest.param(
            [1, 2],
            3,
            Err(
                'Value must be one of: 1, 2 '
                '[kind=literal_error, context={expected: 1, 2}, input_value=3, input_type=int]'
            ),
            id='wrong-multiple-int',
        ),
        (['a', 'b'], 'a', 'a'),
        pytest.param(
            ['a', 'b'],
            'c',
            Err(
                "Value must be one of: 'a', 'b' "
                "[kind=literal_error, context={expected: 'a', 'b'}, input_value=\'c\', input_type=str]"
            ),
            id='wrong-multiple-str',
        ),
        ([1, '1'], 1, 1),
        ([1, '1'], '1', '1'),
        pytest.param(
            [1, '1'],
            '2',
            Err(
                "Value must be one of: 1, '1' "
                "[kind=literal_error, context={expected: 1, '1'}, input_value='2', input_type=str]"
            ),
            id='wrong-str-int',
        ),
    ],
)
def test_literal_py_or_json(py_or_json, kwarg_expected, input_value, expected):
    v = py_or_json({'type': 'literal', 'expected': kwarg_expected})
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
            Err(
                "Value must be one of: 1, b'whatever' "
                "[kind=literal_error, context={expected: 1, b'whatever'}, input_value=3, input_type=int]"
            ),
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
    with pytest.raises(SchemaError, match='SchemaError: "expected" must have length > 0'):
        SchemaValidator({'type': 'literal', 'expected': []})
