import re

import pytest

from pydantic_core import ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        ({1: 2, 3: 4}, [1, 3]),
        ('123', [1, 2, 3]),
        (5, Err('Input should be iterable [kind=iterable_type, input_value=5, input_type=int]')),
        (
            [1, 'wrong'],
            Err(
                'Input should be a valid integer, unable to parse string as an integer '
                "[kind=int_parsing, input_value='wrong', input_type=str]"
            ),
        ),
    ],
    ids=repr,
)
def test_generator_json_int(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            list(v.validate_test(input_value))

    else:
        assert list(v.validate_test(input_value)) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, '3']),
        ({'1': 2, '3': 4}, ['1', '3']),
        ('123', ['1', '2', '3']),
        (5, Err('Input should be iterable [kind=iterable_type, input_value=5, input_type=int]')),
        ([1, 'wrong'], [1, 'wrong']),
    ],
    ids=repr,
)
def test_generator_json_any(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'generator'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            list(v.validate_test(input_value))

    else:
        assert list(v.validate_test(input_value)) == expected


def test_error_index(py_and_json: PyAndJson):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}})
    gen = v.validate_test(['wrong'])
    assert gen.index == 0
    with pytest.raises(ValidationError) as exc_info:
        next(gen)
    assert gen.index == 1
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.title == 'ValidatorIterator'
    assert str(exc_info.value).startswith('1 validation error for ValidatorIterator\n')
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [0],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]
    gen = v.validate_test([1, 2, 3, 'wrong', 4])
    assert gen.index == 0
    assert next(gen) == 1
    assert gen.index == 1
    assert next(gen) == 2
    assert gen.index == 2
    assert next(gen) == 3
    assert gen.index == 3
    with pytest.raises(ValidationError) as exc_info:
        next(gen)
    assert gen.index == 4
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [3],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]
    assert next(gen) == 4
    assert gen.index == 5


def test_too_long(py_and_json: PyAndJson):
    v = py_and_json({'type': 'generator', 'items_schema': {'type': 'int'}, 'max_length': 2})
    assert list(v.validate_test([1])) == [1]
    assert list(v.validate_test([1, 2])) == [1, 2]
    with pytest.raises(ValidationError) as exc_info:
        list(v.validate_test([1, 2, 3]))
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'Generator should have at most 2 items after validation, not 3',
            'input_value': [1, 2, 3],
            'context': {'field_type': 'Generator', 'max_length': 2, 'actual_length': 3},
        }
    ]
