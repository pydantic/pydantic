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
            Err(
                'Input should be 1 [kind=literal_error, input_value=2, input_type=int]',
                [
                    {
                        'kind': 'literal_error',
                        'loc': [],
                        'message': 'Input should be 1',
                        'input_value': 2,
                        'context': {'expected': '1'},
                    }
                ],
            ),
            id='wrong-single-int',
        ),
        (['foo'], 'foo', 'foo'),
        pytest.param(
            ['foo'],
            'bar',
            Err(
                "Input should be 'foo' [kind=literal_error, input_value='bar', input_type=str]",
                [
                    {
                        'kind': 'literal_error',
                        'loc': [],
                        'message': "Input should be 'foo'",
                        'input_value': 'bar',
                        'context': {'expected': "'foo'"},
                    }
                ],
            ),
            id='wrong-single-str',
        ),
        ([1, 2], 1, 1),
        ([1, 2], 2, 2),
        pytest.param(
            [1, 2],
            3,
            Err('Input should be 1 or 2 [kind=literal_error, input_value=3, input_type=int]'),
            id='wrong-multiple-int',
        ),
        ([1, 2, 3, 4], 4, 4),
        pytest.param(
            [1, 2, 3, 4],
            5,
            Err(
                'Input should be 1, 2, 3 or 4 [kind=literal_error, input_value=5, input_type=int]',
                [
                    {
                        'kind': 'literal_error',
                        'loc': [],
                        'message': 'Input should be 1, 2, 3 or 4',
                        'input_value': 5,
                        'context': {'expected': '1, 2, 3 or 4'},
                    }
                ],
            ),
            id='wrong-multiple-int',
        ),
        (['a', 'b'], 'a', 'a'),
        pytest.param(
            ['a', 'b'],
            'c',
            Err("Input should be 'a' or 'b' [kind=literal_error, input_value=\'c\', input_type=str]"),
            id='wrong-multiple-str',
        ),
        ([1, '1'], 1, 1),
        ([1, '1'], '1', '1'),
        pytest.param(
            [1, '1'],
            '2',
            Err(
                "Input should be 1 or '1' [kind=literal_error, input_value='2', input_type=str]",
                [
                    {
                        'kind': 'literal_error',
                        'loc': [],
                        'message': "Input should be 1 or '1'",
                        'input_value': '2',
                        'context': {'expected': "1 or '1'"},
                    }
                ],
            ),
            id='wrong-str-int',
        ),
    ],
)
def test_literal_py_and_json(py_and_json: PyAndJson, kwarg_expected, input_value, expected):
    v = py_and_json({'type': 'literal', 'expected': kwarg_expected})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
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
            Err("Input should be 1 or b'whatever' [kind=literal_error, input_value=3, input_type=int]"),
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


def test_union():
    v = SchemaValidator(core_schema.union_schema(core_schema.literal_schema('a', 'b'), core_schema.int_schema()))
    assert v.validate_python('a') == 'a'
    assert v.validate_python(4) == 4
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('c')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'literal_error',
            'loc': ["literal['a','b']"],
            'message': "Input should be 'a' or 'b'",
            'input_value': 'c',
            'context': {'expected': "'a' or 'b'"},
        },
        {
            'kind': 'int_parsing',
            'loc': ['int'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'c',
        },
    ]
