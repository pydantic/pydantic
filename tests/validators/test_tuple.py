import re
from typing import Any, Dict, Type

import pytest
from dirty_equals import IsNonNegative, IsTuple

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'mode,items,input_value,expected',
    [
        ('variable', {'type': 'int'}, [1, 2, 3], (1, 2, 3)),
        (
            'variable',
            {'type': 'int'},
            1,
            Err('Value must be a valid tuple [kind=tuple_type, input_value=1, input_type=int]'),
        ),
        ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], [1, 2, '3'], (1, 2, 3)),
        (
            'positional',
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            5,
            Err('Value must be a valid tuple [kind=tuple_type, input_value=5, input_type=int]'),
        ),
    ],
    ids=repr,
)
def test_tuple_json(py_and_json: PyAndJson, mode, items, input_value, expected):
    v = py_and_json({'type': 'tuple', 'mode': mode, 'items_schema': items})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_any_no_copy():
    v = SchemaValidator('tuple')
    input_value = (1, '2', b'3')
    output = v.validate_python(input_value)
    assert output == input_value
    assert output is input_value
    assert id(output) == id(input_value)


@pytest.mark.parametrize(
    'mode,items,input_value,expected',
    [
        ('variable', {'type': 'int'}, (1, 2, '33'), (1, 2, 33)),
        ('variable', {'type': 'str'}, (1, 2, '33'), ('1', '2', '33')),
        ('positional', [{'type': 'int'}, {'type': 'str'}, {'type': 'float'}], (1, 2, 33), (1, '2', 33.0)),
    ],
)
def test_tuple_strict_passes_with_tuple(mode, items, input_value, expected):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items, 'strict': True})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'mode,items', [('variable', {'type': 'int'}), ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])]
)
@pytest.mark.parametrize('wrong_coll_type', [list, set, frozenset])
def test_tuple_strict_fails_without_tuple(wrong_coll_type: Type[Any], mode, items):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items, 'strict': True})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(wrong_coll_type([1, 2, '33']))
    assert exc_info.value.errors() == [
        {
            'kind': 'tuple_type',
            'loc': [],
            'message': 'Value must be a valid tuple',
            'input_value': wrong_coll_type([1, 2, '33']),
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2), Err('Input must have at least 3 items [kind=too_short')),
        ({'max_items': 4}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'max_items': 3}, (1, 2, 3, 4), Err('Input must have at most 3 items [kind=too_long')),
    ],
)
def test_tuple_var_len_kwargs(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'tuple', 'mode': 'variable', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'mode,items', [('variable', {'type': 'int'}), ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])]
)
@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, '3'), (1, 2, 3)),
        ({1, 2, '3'}, IsTuple(1, 2, 3, check_order=False)),
        (frozenset([1, 2, '3']), IsTuple(1, 2, 3, check_order=False)),
    ],
)
def test_tuple_validate(input_value, expected, mode, items):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,index',
    [
        (['wrong'], 0),
        (('wrong',), 0),
        ({'wrong'}, 0),
        ((1, 2, 3, 'wrong'), 3),
        ((1, 2, 3, 'wrong', 4), 3),
        ((1, 2, 'wrong'), IsNonNegative()),
    ],
)
def test_tuple_var_len_errors(input_value, index):
    v = SchemaValidator({'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}})
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
    'input_value,items,index',
    [
        (['wrong'], [{'type': 'int'}], 0),
        (('wrong',), [{'type': 'int'}], 0),
        ({'wrong'}, [{'type': 'int'}], 0),
        ((1, 2, 3, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}], 3),
        (
            (1, 2, 3, 'wrong', 4),
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            3,
        ),
        ((1, 2, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], IsNonNegative()),
    ],
)
def test_tuple_fix_len_errors(input_value, items, index):
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': items})
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
    'items,input_value,expected',
    [
        ([{'type': 'int'}], [1, 2, 3], Err('Input must have at most 1 items [kind=too_long')),
        ([{'type': 'int'}, {'type': 'int'}], [1], Err('Input must have at least 2 items [kind=too_short')),
    ],
    ids=['input too long', 'input too short'],
)
def test_tuple_fix_len_input_and_schemas_len_mismatch(items, input_value, expected):
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': items})
    with pytest.raises(ValidationError, match=re.escape(expected.message)):
        v.validate_python(input_value)


def test_tuple_fix_len_schema_error():
    with pytest.raises(SchemaError, match='SchemaError: Empty positional items schema'):
        SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': []})


@pytest.mark.parametrize('input_value,expected', [((1, 2, 3), (1, 2, 3)), ([1, 2, 3], [1, 2, 3])])
def test_union_tuple_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'tuple', 'mode': 'variable'}, {'type': 'list'}]})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (('a', 1, 'c'), ('a', '1', 'c')),
        (
            [5],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        # first of all, not a tuple of ints ..
                        'kind': 'tuple_type',
                        'loc': ['tuple[int, ...]'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5],
                    },
                    # .. and not a tuple of strings, either
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[str, ...]'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5],
                    },
                ],
            ),
        ),
    ],
)
def test_union_tuple_var_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}, 'strict': True},
                {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'str'}, 'strict': True},
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


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (('a', 1, 'c'), ('a', '1', 'c')),
        (
            [5, '1', 1],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[int, int, int]'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[str, str, str]'],
                        'message': 'Value must be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                ],
            ),
        ),
    ],
)
def test_union_tuple_fix_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'tuple',
                    'mode': 'positional',
                    'items_schema': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
                    'strict': True,
                },
                {
                    'type': 'tuple',
                    'mode': 'positional',
                    'items_schema': [{'type': 'str'}, {'type': 'str'}, {'type': 'str'}],
                    'strict': True,
                },
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


def test_tuple_fix_error():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'str']})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])

    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': [],
            'message': 'Input must have at least 2 items',
            'input_value': [1],
            'context': {'min_length': 2},
        }
    ]


def test_tuple_fix_extra():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'str'], 'extra_schema': 'str'})
    assert v.validate_python([1, 'a']) == (1, 'a')
    assert v.validate_python((1, 'a')) == (1, 'a')
    assert v.validate_python((1, 'a', 'b')) == (1, 'a', 'b')
    assert v.validate_python([1, 'a', 'b', 'c', 'd']) == (1, 'a', 'b', 'c', 'd')
    with pytest.raises(ValidationError, match='Input must have at least 2 items'):
        v.validate_python([1])


def test_tuple_fix_extra_any():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['str'], 'extra_schema': 'any'})
    assert v.validate_python([1]) == ('1',)
    assert v.validate_python([1, 2]) == ('1', 2)
    assert v.validate_python((1, 2)) == ('1', 2)
    assert v.validate_python([1, 2, b'3']) == ('1', 2, b'3')
    with pytest.raises(ValidationError, match='Input must have at least 1 items'):
        v.validate_python([])
