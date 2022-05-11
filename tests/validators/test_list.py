import pytest
from dirty_equals import IsList, IsNonNegative

from pydantic_core import SchemaValidator, ValidationError


@pytest.mark.parametrize('input_value,expected', [([1, 2, 3], [1, 2, 3]), ([1, 2, '3'], [1, 2, 3])])
def test_list_json(py_or_json, input_value, expected):
    v = py_or_json({'type': 'list', 'items': {'type': 'int'}})
    assert v.validate_test(input_value) == expected


def test_list_strict():
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}, 'strict': True})
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
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}})
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
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}})
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
