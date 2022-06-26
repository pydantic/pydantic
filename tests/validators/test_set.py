import re

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], set()),
        ([1, 2, 3], {1, 2, 3}),
        ([1, 2, '3'], {1, 2, 3}),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        (5, Err('Value must be a valid set [kind=set_type, input_value=5, input_type=int]')),
    ],
)
def test_set_ints_both(py_or_json, input_value, expected):
    v = py_or_json({'type': 'set', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'})])
def test_set_no_validators_both(py_or_json, input_value, expected):
    v = py_or_json({'type': 'set'})
    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2.5, '3'], {1, 2.5, '3'}),
        ('foo', Err('Value must be a valid set')),
        (1, Err('Value must be a valid set')),
        (1.0, Err('Value must be a valid set')),
        (False, Err('Value must be a valid set')),
    ],
)
def test_frozenset_no_validators_both(py_or_json, input_value, expected):
    v = py_or_json({'type': 'set'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        (set(), set()),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        ([], set()),
        ((1, 2, 3, 2, 3), {1, 2, 3}),
        ((), set()),
        (frozenset([1, 2, 3, 2, 3]), {1, 2, 3}),
        ({'abc'}, Err('0\n  Value must be a valid integer')),
        ({1: 2}, Err('1 validation error for set[int]\n  Value must be a valid set')),
        ('abc', Err('Value must be a valid set')),
        # Technically correct, but does anyone actually need this? I think needs a new type in pyo3
        pytest.param({1: 10, 2: 20, 3: 30}.keys(), {1, 2, 3}, marks=pytest.mark.xfail(raises=ValidationError)),
    ],
)
def test_set_ints_python(input_value, expected):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'}), ([(1, 2), (3, 4)], {(1, 2), (3, 4)})])
def test_set_no_validators_python(input_value, expected):
    v = SchemaValidator({'type': 'set'})
    assert v.validate_python(input_value) == expected


def test_set_multiple_errors():
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(['a', (1, 2), []])
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [0],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'a',
        },
        {'kind': 'int_type', 'loc': [1], 'message': 'Value must be a valid integer', 'input_value': (1, 2)},
        {'kind': 'int_type', 'loc': [2], 'message': 'Value must be a valid integer', 'input_value': []},
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({'strict': True}, {1, 2, 3}, {1, 2, 3}),
        ({'strict': True}, set(), set()),
        ({'strict': True}, [1, 2, 3, 2, 3], Err('Value must be a valid set [kind=set_type,')),
        ({'strict': True}, [], Err('Value must be a valid set [kind=set_type,')),
        ({'strict': True}, (), Err('Value must be a valid set [kind=set_type,')),
        ({'strict': True}, (1, 2, 3), Err('Value must be a valid set [kind=set_type,')),
        ({'strict': True}, frozenset([1, 2, 3]), Err('Value must be a valid set [kind=set_type,')),
        ({'strict': True}, 'abc', Err('Value must be a valid set [kind=set_type,')),
        ({'min_items': 3}, {1, 2, 3}, {1, 2, 3}),
        ({'min_items': 3}, {1, 2}, Err('Set must have at least 3 items [kind=too_short,')),
        ({'max_items': 3}, {1, 2, 3}, {1, 2, 3}),
        ({'max_items': 3}, {1, 2, 3, 4}, Err('Set must have at most 3 items [kind=too_long,')),
    ],
)
def test_set_kwargs(kwargs, input_value, expected):
    v = SchemaValidator({'type': 'set', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [({1, 2, 3}, {1, 2, 3}), ([1, 2, 3], [1, 2, 3])])
def test_union_set_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'set'}, {'type': 'list'}]})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        ({'a', 'b', 'c'}, {'a', 'b', 'c'}),
        (
            [1, 'a'],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'kind': 'int_type',
                        'loc': ['set[strict-int]', 1],
                        'message': 'Value must be a valid integer',
                        'input_value': 'a',
                    },
                    # second because validation on the string choice comes second
                    {
                        'kind': 'str_type',
                        'loc': ['set[strict-str]', 0],
                        'message': 'Value must be a valid string',
                        'input_value': 1,
                    },
                ],
            ),
        ),
    ],
)
def test_union_set_int_set_str(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'set', 'items_schema': {'type': 'int', 'strict': True}},
                {'type': 'set', 'items_schema': {'type': 'str', 'strict': True}},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


def test_set_as_dict_keys(py_or_json):
    v = py_or_json({'type': 'dict', 'keys_schema': {'type': 'set'}, 'value': 'int'})
    with pytest.raises(ValidationError, match=re.escape('Value must be a valid set')):
        v.validate_test({'foo': 'bar'})
