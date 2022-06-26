import re

import pytest
from dirty_equals import IsList, IsNonNegative

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        (5, Err('Value must be a valid list/array [kind=list_type, input_value=5, input_type=int]')),
        ('5', Err("Value must be a valid list/array [kind=list_type, input_value='5', input_type=str]")),
    ],
)
def test_list_json(py_or_json, input_value, expected):
    v = py_or_json({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_list_strict():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'strict': True})
    assert v.validate_python([1, 2, '33']) == [1, 2, 33]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python((1, 2, '33'))
    assert exc_info.value.errors() == [
        {'kind': 'list_type', 'loc': [], 'message': 'Value must be a valid list/array', 'input_value': (1, 2, '33')}
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, '3'), [1, 2, 3]),
        ({1, 2, '3'}, IsList(1, 2, 3, check_order=False)),
        (frozenset([1, 2, '3']), IsList(1, 2, 3, check_order=False)),
    ],
)
def test_list(input_value, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,index',
    [
        (['wrong'], 0),
        (('wrong',), 0),
        ({'wrong'}, 0),
        ([1, 2, 3, 'wrong'], 3),
        ((1, 2, 3, 'wrong', 4), 3),
        ({1, 2, 'wrong'}, IsNonNegative()),
    ],
)
def test_list_error(input_value, index):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_items': 3}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_items': 3}, [1, 2], Err('List must have at least 3 items [kind=too_short')),
        ({'max_items': 4}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'max_items': 3}, [1, 2, 3, 4], Err('List must have at most 3 items [kind=too_long')),
    ],
)
def test_list_length_constraints(kwargs, input_value, expected):
    v = SchemaValidator({'type': 'list', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected
